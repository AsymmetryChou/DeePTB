from typing import Optional, List, Union, Dict
import math
import functools
import torch
from torch_runstats.scatter import scatter

from torch import fx
from e3nn.util.codegen import CodeGenMixin
from e3nn import o3
from e3nn.nn import Gate
from torch_scatter import scatter_mean
from e3nn.o3 import Linear, SphericalHarmonics
from e3nn.math import normalize2mom
from e3nn.util.jit import compile_mode
from dptb.data import AtomicDataDict
from dptb.nn.embedding.emb import Embedding
from ..radial_basis import BesselBasis
from dptb.nn.embedding.from_deephe3.deephe3 import tp_path_exists
from dptb.data import _keys
from dptb.nn.cutoff import cosine_cutoff, polynomial_cutoff
from dptb.nn.rescale import E3ElementLinear
from dptb.nn.tensor_product import SO2_Linear
import math
from dptb.data.transforms import OrbitalMapper
from ..type_encode.one_hot import OneHotAtomEncoding
from dptb.data.AtomicDataDict import with_edge_vectors, with_batch

from math import ceil

@Embedding.register("e3baseline_3")
class E3BaseLineModel3(torch.nn.Module):
    def __init__(
            self,
            basis: Dict[str, Union[str, list]]=None,
            idp: Union[OrbitalMapper, None]=None,
            # required params
            n_atom: int=1,
            n_layers: int=3,
            n_radial_basis: int=10,
            r_max: float=5.0,
            lmax: int=4,
            irreps_hidden: o3.Irreps=None,
            avg_num_neighbors: Optional[float] = None,
            # cutoffs
            r_start_cos_ratio: float = 0.8,
            PolynomialCutoff_p: float = 6,
            cutoff_type: str = "polynomial",
            # general hyperparameters:
            linear_after_env_embed: bool = False,
            env_embed_multiplicity: int = 32,
            sh_normalized: bool = True,
            sh_normalization: str = "component",
            # MLP parameters:
            latent_kwargs={
                "mlp_latent_dimensions": [256, 256, 512],
                "mlp_nonlinearity": "silu",
                "mlp_initialization": "uniform"
            },
            latent_resnet: bool = True,
            latent_resnet_update_ratios: Optional[List[float]] = None,
            latent_resnet_update_ratios_learnable: bool = False,
            dtype: Union[str, torch.dtype] = torch.float32,
            device: Union[str, torch.device] = torch.device("cpu"),
            ):
        
        super(E3BaseLineModel3, self).__init__()

        irreps_hidden = o3.Irreps(irreps_hidden)

        if isinstance(dtype, str):
            dtype = getattr(torch, dtype)
        self.dtype = dtype
        if isinstance(device, str):
            device = torch.device(device)
        self.device = device
        
        if basis is not None:
            self.idp = OrbitalMapper(basis, method="e3tb")
            if idp is not None:
                assert idp == self.idp, "The basis of idp and basis should be the same."
        else:
            assert idp is not None, "Either basis or idp should be provided."
            self.idp = idp
            
        self.basis = self.idp.basis
        self.idp.get_irreps(no_parity=False)
        self.n_atom = n_atom

        irreps_sh=o3.Irreps([(1, (i, (-1) ** i)) for i in range(lmax + 1)])
        orbpair_irreps = self.idp.orbpair_irreps.sort()[0].simplify()

        # check if the irreps setting satisfied the requirement of idp
        irreps_out = []
        for mul, ir1 in irreps_hidden:
            for _, ir2 in orbpair_irreps:
                irreps_out += [o3.Irrep(str(irr)) for irr in ir1*ir2]
        irreps_out = o3.Irreps(irreps_out).sort()[0].simplify()

        assert all(ir in irreps_out for _, ir in orbpair_irreps), "hidden irreps should at least cover all the reqired irreps in the hamiltonian data {}".format(orbpair_irreps)
        
        # TODO: check if the tp in first layer can produce the required irreps for hidden states

        self.sh = SphericalHarmonics(
            irreps_sh, sh_normalized, sh_normalization
        )
        self.onehot = OneHotAtomEncoding(num_types=n_atom, set_features=False)

        self.init_layer = InitLayer(
            idp=self.idp,
            num_types=n_atom,
            n_radial_basis=n_radial_basis,
            r_max=r_max,
            irreps_sh=irreps_sh,
            env_embed_multiplicity=env_embed_multiplicity,
            # MLP parameters:
            two_body_latent_kwargs=latent_kwargs,
            env_embed_kwargs = {
                "mlp_latent_dimensions": [],
                "mlp_nonlinearity": None,
                "mlp_initialization": "uniform"
            },
            # cutoffs
            r_start_cos_ratio=r_start_cos_ratio,
            PolynomialCutoff_p=PolynomialCutoff_p,
            cutoff_type=cutoff_type,
            device=device,
            dtype=dtype,
        )

        self.layers = torch.nn.ModuleList()
        latent_in =latent_kwargs["mlp_latent_dimensions"][-1]
        # actually, we can derive the least required irreps_in and out from the idp's node and pair irreps
        last_layer = False
        for i in range(n_layers):
            if i == 0:
                irreps_in = self.init_layer.irreps_out
            else:
                irreps_in = irreps_hidden
            
            if i == n_layers - 1:
                irreps_out = orbpair_irreps.sort()[0].simplify()
                last_layer = True
            else:
                irreps_out = irreps_hidden

            self.layers.append(Layer(
                num_types=n_atom,
                avg_num_neighbors=avg_num_neighbors,
                irreps_sh=irreps_sh,
                irreps_in=irreps_in,
                irreps_out=irreps_out,
                # general hyperparameters:
                linear_after_env_embed=linear_after_env_embed,
                env_embed_multiplicity=env_embed_multiplicity,
                # MLP parameters:
                latent_kwargs=latent_kwargs,
                latent_in=latent_in,
                latent_resnet=latent_resnet,
                latent_resnet_update_ratios=latent_resnet_update_ratios,
                latent_resnet_update_ratios_learnable=latent_resnet_update_ratios_learnable,
                last_layer=last_layer,
                dtype=dtype,
                device=device,
                )
            )

        # initilize output_layer
        self.out_edge = Linear(self.layers[-1].irreps_out, self.idp.orbpair_irreps, shared_weights=True, internal_weights=True, biases=True)
        self.out_node = Linear(self.layers[-1].irreps_out, self.idp.orbpair_irreps, shared_weights=True, internal_weights=True, biases=True)

    @property
    def out_edge_irreps(self):
        return self.idp.orbpair_irreps

    @property
    def out_node_irreps(self):
        return self.idp.orbpair_irreps
    
    def forward(self, data: AtomicDataDict.Type) -> AtomicDataDict.Type:
        data = with_edge_vectors(data, with_lengths=True)
        # data = with_env_vectors(data, with_lengths=True)
        data = with_batch(data)

        edge_index = data[_keys.EDGE_INDEX_KEY]
        edge_vector = data[_keys.EDGE_VECTORS_KEY]
        edge_sh = self.sh(data[_keys.EDGE_VECTORS_KEY][:,[1,2,0]])
        edge_length = data[_keys.EDGE_LENGTH_KEY]

        
        data = self.onehot(data)
        node_one_hot = data[_keys.NODE_ATTRS_KEY]
        atom_type = data[_keys.ATOM_TYPE_KEY].flatten()
        bond_type = data[_keys.EDGE_TYPE_KEY].flatten()
        latents, features, cutoff_coeffs, active_edges = self.init_layer(edge_index, bond_type, edge_sh, edge_length, node_one_hot)
    
        for layer in self.layers:
            latents, features, cutoff_coeffs, active_edges = layer(edge_index, edge_vector, edge_sh, atom_type, latents, features, cutoff_coeffs, active_edges)
        
        data[_keys.NODE_FEATURES_KEY] = self.out_node(latents)
        data[_keys.EDGE_FEATURES_KEY] = torch.zeros(edge_index.shape[1], self.idp.orbpair_irreps.dim, dtype=self.dtype, device=self.device)
        data[_keys.EDGE_FEATURES_KEY] = torch.index_copy(data[_keys.EDGE_FEATURES_KEY], 0, active_edges, self.out_edge(features))

        return data
    
@torch.jit.script
def ShiftedSoftPlus(x: torch.Tensor):
    return torch.nn.functional.softplus(x) - math.log(2.0)

class ScalarMLPFunction(CodeGenMixin, torch.nn.Module):
    """Module implementing an MLP according to provided options."""

    in_features: int
    out_features: int

    def __init__(
        self,
        mlp_input_dimension: Optional[int],
        mlp_latent_dimensions: List[int],
        mlp_output_dimension: Optional[int],
        mlp_nonlinearity: Optional[str] = "silu",
        mlp_initialization: str = "normal",
        mlp_dropout_p: float = 0.0,
        mlp_batchnorm: bool = False,
    ):
        super().__init__()
        nonlinearity = {
            None: None,
            "silu": torch.nn.functional.silu,
            "ssp": ShiftedSoftPlus,
        }[mlp_nonlinearity]
        if nonlinearity is not None:
            nonlin_const = normalize2mom(nonlinearity).cst
        else:
            nonlin_const = 1.0

        dimensions = (
            ([mlp_input_dimension] if mlp_input_dimension is not None else [])
            + mlp_latent_dimensions
            + ([mlp_output_dimension] if mlp_output_dimension is not None else [])
        )
        assert len(dimensions) >= 2  # Must have input and output dim
        num_layers = len(dimensions) - 1

        self.in_features = dimensions[0]
        self.out_features = dimensions[-1]

        # Code
        params = {}
        graph = fx.Graph()
        tracer = fx.proxy.GraphAppendingTracer(graph)

        def Proxy(n):
            return fx.Proxy(n, tracer=tracer)

        features = Proxy(graph.placeholder("x"))
        norm_from_last: float = 1.0

        base = torch.nn.Module()

        for layer, (h_in, h_out) in enumerate(zip(dimensions, dimensions[1:])):
            # do dropout
            if mlp_dropout_p > 0:
                # only dropout if it will do something
                # dropout before linear projection- https://stats.stackexchange.com/a/245137
                features = Proxy(graph.call_module("_dropout", (features.node,)))

            # make weights
            w = torch.empty(h_in, h_out)

            if mlp_initialization == "normal":
                w.normal_()
            elif mlp_initialization == "uniform":
                # these values give < x^2 > = 1
                w.uniform_(-math.sqrt(3), math.sqrt(3))
            elif mlp_initialization == "orthogonal":
                # this rescaling gives < x^2 > = 1
                torch.nn.init.orthogonal_(w, gain=math.sqrt(max(w.shape)))
            else:
                raise NotImplementedError(
                    f"Invalid mlp_initialization {mlp_initialization}"
                )

            # generate code
            params[f"_weight_{layer}"] = w
            w = Proxy(graph.get_attr(f"_weight_{layer}"))
            w = w * (
                norm_from_last / math.sqrt(float(h_in))
            )  # include any nonlinearity normalization from previous layers
            features = torch.matmul(features, w)

            if mlp_batchnorm:
                # if we call batchnorm, do it after the nonlinearity
                features = Proxy(graph.call_module(f"_bn_{layer}", (features.node,)))
                setattr(base, f"_bn_{layer}", torch.nn.BatchNorm1d(h_out))

            # generate nonlinearity code
            if nonlinearity is not None and layer < num_layers - 1:
                features = nonlinearity(features)
                # add the normalization const in next layer
                norm_from_last = nonlin_const

        graph.output(features.node)

        for pname, p in params.items():
            setattr(base, pname, torch.nn.Parameter(p))

        if mlp_dropout_p > 0:
            # with normal dropout everything blows up
            base._dropout = torch.nn.AlphaDropout(p=mlp_dropout_p)

        self._codegen_register({"_forward": fx.GraphModule(base, graph)})

    def forward(self, x):
        return self._forward(x)

class InitLayer(torch.nn.Module):
    def __init__(
            self,
            # required params
            idp,
            num_types: int,
            n_radial_basis: int,
            r_max: float,
            irreps_sh: o3.Irreps=None,
            env_embed_multiplicity: int = 32,
            # MLP parameters:
            two_body_latent_kwargs={
                "mlp_latent_dimensions": [128, 256, 512, 1024],
                "mlp_nonlinearity": "silu",
                "mlp_initialization": "uniform"
            },
            env_embed_kwargs = {
                "mlp_latent_dimensions": [],
                "mlp_nonlinearity": None,
                "mlp_initialization": "uniform"
            },
            # cutoffs
            r_start_cos_ratio: float = 0.8,
            PolynomialCutoff_p: float = 6,
            cutoff_type: str = "polynomial",
            device: Union[str, torch.device] = torch.device("cpu"),
            dtype: Union[str, torch.dtype] = torch.float32,
    ):
        super(InitLayer, self).__init__()
        SCALAR = o3.Irrep("0e")
        self.num_types = num_types
        if isinstance(r_max, float) or isinstance(r_max, int):
            self.r_max = torch.tensor(r_max, device=device, dtype=dtype)
            self.r_max_dict = None
        elif isinstance(r_max, dict):
            c_set = set(list(r_max.values()))
            self.r_max = torch.tensor(max(list(r_max.values())), device=device, dtype=dtype)
            if len(r_max) == 1 or len(c_set) == 1:
                self.r_max_dict = None
            else:
                self.r_max_dict = {}
                for k,v in r_max.items():
                    self.r_max_dict[k] = torch.tensor(v, device=device, dtype=dtype)
        else:
            raise TypeError("r_max should be either float, int or dict")
                  
        self.idp = idp
        self.two_body_latent_kwargs = two_body_latent_kwargs
        self.r_start_cos_ratio = r_start_cos_ratio
        self.polynomial_cutoff_p = PolynomialCutoff_p
        self.cutoff_type = cutoff_type
        self.device = device
        self.dtype = dtype
        self.irreps_out = o3.Irreps([(env_embed_multiplicity, ir) for _, ir in irreps_sh])

        assert all(mul==1 for mul, _ in irreps_sh)
        # env_embed_irreps = o3.Irreps([(1, ir) for _, ir in irreps_sh])
        assert (
            irreps_sh[0].ir == SCALAR
        ), "env_embed_irreps must start with scalars"

        # Node invariants for center and neighbor (chemistry)
        # Plus edge invariants for the edge (radius).
        self.two_body_latent = ScalarMLPFunction(
                        mlp_input_dimension=(2 * num_types + n_radial_basis),
                        mlp_output_dimension=None,
                        **two_body_latent_kwargs,
                    )

        self._env_weighter = Linear(
            irreps_in=irreps_sh,
            irreps_out=self.irreps_out,
            internal_weights=False,
            shared_weights=False,
            path_normalization = "element", # if path normalization is element and input irreps has 1 mul, it should not have effect ! 
        )

        self.env_embed_mlp = ScalarMLPFunction(
                        mlp_input_dimension=self.two_body_latent.out_features,
                        mlp_output_dimension=self._env_weighter.weight_numel,
                        **env_embed_kwargs,
                    )
        
        self.bessel = BesselBasis(r_max=self.r_max, num_basis=n_radial_basis, trainable=True)



    def forward(self, edge_index, bond_type, edge_sh, edge_length, node_one_hot):
        edge_center = edge_index[0]
        edge_neighbor = edge_index[1]

        edge_invariants = self.bessel(edge_length)
        node_invariants = node_one_hot

        # Vectorized precompute per layer cutoffs
        if self.r_max_dict is None:
            if self.cutoff_type == "cosine":
                cutoff_coeffs = cosine_cutoff(
                    edge_length,
                    self.r_max.reshape(-1),
                    r_start_cos_ratio=self.r_start_cos_ratio,
                ).flatten()

            elif self.cutoff_type == "polynomial":
                cutoff_coeffs = polynomial_cutoff(
                    edge_length, self.r_max.reshape(-1), p=self.polynomial_cutoff_p
                ).flatten()

            else:
                # This branch is unreachable (cutoff type is checked in __init__)
                # But TorchScript doesn't know that, so we need to make it explicitly
                # impossible to make it past so it doesn't throw
                # "cutoff_coeffs_all is not defined in the false branch"
                assert False, "Invalid cutoff type"
        else:
            cutoff_coeffs = torch.zeros(edge_index.shape[1], dtype=self.dtype, device=self.device)

            for bond, ty in self.idp.bond_to_type.items():
                mask = bond_type == ty
                index = mask.nonzero().squeeze(-1)

                if mask.any():
                    iatom, jatom = bond.split("-")
                    if self.cutoff_type == "cosine":
                        c_coeff = cosine_cutoff(
                            edge_length[mask],
                            0.5*(self.r_max_dict[iatom]+self.r_max_dict[jatom]),
                            r_start_cos_ratio=self.r_start_cos_ratio,
                        ).flatten()
                    elif self.cutoff_type == "polynomial":
                        c_coeff = polynomial_cutoff(
                            edge_length[mask],
                            0.5*(self.r_max_dict[iatom]+self.r_max_dict[jatom]),
                            p=self.polynomial_cutoff_p
                        ).flatten()

                    else:
                        # This branch is unreachable (cutoff type is checked in __init__)
                        # But TorchScript doesn't know that, so we need to make it explicitly
                        # impossible to make it past so it doesn't throw
                        # "cutoff_coeffs_all is not defined in the false branch"
                        assert False, "Invalid cutoff type"

                    cutoff_coeffs = torch.index_copy(cutoff_coeffs, 0, index, c_coeff)

        # Determine which edges are still in play
        prev_mask = cutoff_coeffs > 0
        active_edges = (cutoff_coeffs > 0).nonzero().squeeze(-1)

        # Compute latents
        latents = torch.zeros(
            (edge_sh.shape[0], self.two_body_latent.out_features),
            dtype=edge_sh.dtype,
            device=edge_sh.device,
        )
        
        new_latents = self.two_body_latent(torch.cat([
            node_invariants[edge_center],
            node_invariants[edge_neighbor],
            edge_invariants,
        ], dim=-1)[prev_mask])

        # Apply cutoff, which propagates through to everything else
        latents = torch.index_copy(
            latents, 0, active_edges, 
            cutoff_coeffs[active_edges].unsqueeze(-1) * new_latents
            )
        weights = self.env_embed_mlp(new_latents)

        # embed initial edge
        features = self._env_weighter(
            edge_sh[prev_mask], weights
        )  # features is edge_attr
        # features = self.bn(features)

        return latents, features, cutoff_coeffs, active_edges # the radial embedding x and the sperical hidden V

class Layer(torch.nn.Module):
    def __init__(
        self,
        # required params
        num_types: int,
        avg_num_neighbors: Optional[float] = None,
        irreps_sh: o3.Irreps=None,
        irreps_in: o3.Irreps=None,
        irreps_out: o3.Irreps=None,
        # general hyperparameters:
        linear_after_env_embed: bool = False,
        env_embed_multiplicity: int = 32,
        # MLP parameters:
        latent_kwargs={
            "mlp_latent_dimensions": [128, 256, 512, 1024],
            "mlp_nonlinearity": "silu",
            "mlp_initialization": "uniform"
        },
        latent_in: int=1024,
        latent_resnet: bool = True,
        last_layer: bool = False,
        latent_resnet_update_ratios: Optional[List[float]] = None,
        latent_resnet_update_ratios_learnable: bool = False,
        dtype: Union[str, torch.dtype] = torch.float32,
        device: Union[str, torch.device] = torch.device("cpu"),
    ):
        super().__init__()

        assert latent_in == latent_kwargs["mlp_latent_dimensions"][-1]

        SCALAR = o3.Irrep("0e")
        self.latent_resnet = latent_resnet
        self.avg_num_neighbors = avg_num_neighbors
        self.linear_after_env_embed = linear_after_env_embed
        self.irreps_in = irreps_in
        self.irreps_out = irreps_out
        self.last_layer = last_layer
        self.dtype = dtype
        self.device = device

        assert all(mul==1 for mul, _ in irreps_sh)

        # for normalization of env embed sums
        # one per layer
        self.register_buffer(
            "env_sum_normalizations",
            # dividing by sqrt(N)
            torch.as_tensor(avg_num_neighbors).rsqrt(),
        )

        latent = functools.partial(ScalarMLPFunction, **latent_kwargs)

        self.latents = None
        self.env_embed_mlps = None
        self.tps = None
        self.linears = None
        self.env_linears = None

        # Prune impossible paths
        self.irreps_out = o3.Irreps(
                [
                    (mul, ir)
                    for mul, ir in self.irreps_out
                    if tp_path_exists(irreps_sh, irreps_in, ir)
                ]
            )

        mul_irreps_sh = o3.Irreps([(env_embed_multiplicity, ir) for _, ir in irreps_sh])
        self._env_weighter = Linear(
            irreps_in=irreps_sh,
            irreps_out=mul_irreps_sh,
            internal_weights=False,
            shared_weights=False,
            path_normalization = "element",
        )

        if last_layer:
            self._node_weighter = E3ElementLinear(
                irreps_in=irreps_out,
                dtype=dtype,
                device=device,
            )

            self._edge_weighter = E3ElementLinear(
                irreps_in=irreps_out,
                dtype=dtype,
                device=device,
            )

        # build activation
        
        irreps_scalar = o3.Irreps([(mul, ir) for mul, ir in self.irreps_out if ir.l == 0]).simplify()
        irreps_gated = o3.Irreps([(mul, ir) for mul, ir in self.irreps_out if ir.l > 0]).simplify()
        
        
        irreps_gates = o3.Irreps([(mul, (0,1)) for mul, _ in irreps_gated]).simplify()
        act={1: torch.nn.functional.silu, -1: torch.tanh}
        act_gates={1: torch.sigmoid, -1: torch.tanh}

        self.activation = Gate(
            irreps_scalar, [act[ir.p] for _, ir in irreps_scalar],  # scalar
            irreps_gates, [act_gates[ir.p] for _, ir in irreps_gates],  # gates (scalars)
            irreps_gated  # gated tensors
        )
        
        self.tp = SO2_Linear(
            irreps_in=self.irreps_in+self._env_weighter.irreps_out,
            irreps_out=self.activation.irreps_in,
        )

        if self.last_layer:
            self.tp_out = SO2_Linear(
                irreps_in=self.irreps_out+self._env_weighter.irreps_out+self._env_weighter.irreps_out,
                irreps_out=self.irreps_out,
            )
    
        self.lin_post = Linear(
            self.activation.irreps_out,
            self.irreps_out,
            shared_weights=True, 
            internal_weights=True,
            biases=True,
        )

        if latent_resnet:
            self.linear_res = Linear(
                self.irreps_in,
                self.irreps_out,
                shared_weights=True, 
                internal_weights=True,
                biases=True,
            )
        
        # the embedded latent invariants from the previous layer(s)
        # and the invariants extracted from the last layer's TP:
        # we need to make sure all scalars in tp.irreps_out all contains in the first irreps
        all_tp_scalar = o3.Irreps([(mul, ir) for mul, ir in self.tp.irreps_out if ir.l == 0]).simplify()
        assert all_tp_scalar.dim == self.tp.irreps_out[0].dim
        self.latents = latent(
            mlp_input_dimension=latent_in+self.tp.irreps_out[0].dim,
            mlp_output_dimension=None,
        )
        
        # the env embed MLP takes the last latent's output as input
        # and outputs enough weights for the env embedder
        self.env_embed_mlps = ScalarMLPFunction(
                mlp_input_dimension=latent_in,
                mlp_latent_dimensions=[],
                mlp_output_dimension=self._env_weighter.weight_numel,
            )
        
        if last_layer:
            self.node_embed_mlps = ScalarMLPFunction(
                mlp_input_dimension=latent_in,
                mlp_latent_dimensions=[],
                mlp_output_dimension=self._node_weighter.weight_numel,
            )
            
            self.edge_embed_mlps = ScalarMLPFunction(
                mlp_input_dimension=latent_in,
                mlp_latent_dimensions=[],
                mlp_output_dimension=self._edge_weighter.weight_numel,
            )
            
        # - layer resnet update weights -
        if latent_resnet_update_ratios is None:
            # We initialize to zeros, which under the sigmoid() become 0.5
            # so 1/2 * layer_1 + 1/4 * layer_2 + ...
            # note that the sigmoid of these are the factor _between_ layers
            # so the first entry is the ratio for the latent resnet of the first and second layers, etc.
            # e.g. if there are 3 layers, there are 2 ratios: l1:l2, l2:l3
            latent_resnet_update_params = torch.zeros(1)
        else:
            latent_resnet_update_ratios = torch.as_tensor(
                latent_resnet_update_ratios, dtype=torch.get_default_dtype()
            )
            assert latent_resnet_update_ratios > 0.0
            assert latent_resnet_update_ratios < 1.0
            latent_resnet_update_params = torch.special.logit(
                latent_resnet_update_ratios
            )
            # The sigmoid is mostly saturated at ±6, keep it in a reasonable range
            latent_resnet_update_params.clamp_(-6.0, 6.0)
        
        if latent_resnet_update_ratios_learnable:
            self._latent_resnet_update_params = torch.nn.Parameter(
                latent_resnet_update_params
            )
        else:
            self.register_buffer(
                "_latent_resnet_update_params", latent_resnet_update_params
            )

    def forward(self, edge_index, edge_vector, edge_sh, atom_type, latents, features, cutoff_coeffs, active_edges):
        # update V
        # update X
        # edge_index: [2, num_edges]
        # irreps_sh: [num_edges, irreps_sh]
        # latents: [num_edges, latent_in]
        # fetures: [num_active_edges, in_irreps]
        # cutoff_coeffs: [num_edges]
        # active_edges: [num_active_edges]

        edge_center = edge_index[0]
        edge_neighbor = edge_index[1]

        prev_mask = cutoff_coeffs > 0

        # sc_features = self.sc(features, node_one_hot[edge_index].transpose(0,1).flatten(1,2)[active_edges])
        # update V
        weights = self.env_embed_mlps(latents[active_edges])

        # Build the local environments
        # This local environment should only be a sum over neighbors
        # who are within the cutoff of the _current_ layer
        # Those are the active edges, which are the only ones we
        # have weights for (env_w) anyway.
        # So we mask out the edges in the sum:
        local_env_per_edge = scatter(
            self._env_weighter(edge_sh[active_edges], weights),
            edge_center[active_edges],
            dim=0,
        )

        # currently, we have a sum over neighbors of constant number for each layer,
        # the env_sum_normalization can be a scalar or list
        # the different cutoff can be added in the future
        
        if self.env_sum_normalizations.ndim < 1:
            norm_const = self.env_sum_normalizations
        else:
            norm_const = self.env_sum_normalizations[atom_type.flatten()].unsqueeze(-1)
        
        local_env_per_edge = local_env_per_edge * norm_const
        # Now do the TP
        # recursively tp current features with the environment embeddings
        new_features = self.tp(
            torch.cat(
                [features, local_env_per_edge[edge_center[active_edges]]]
                , dim=-1), edge_vector[active_edges]) # full_out_irreps
        
        scalars = new_features[:, :self.tp.irreps_out[0].dim]
        new_features = self.activation(new_features)
        # # do the linear
        # features has shape [N_edge, full_feature_out.dim]
        # we know scalars are first
        assert len(scalars.shape) == 2

        new_features = self.lin_post(new_features)

        # new_features = self.bn(new_features, bond_type[active_edges])
        # new_features = new_features - scatter_mean(new_features, batch[edge_center[active_edges]], dim=0, dim_size=batch.max()+1)[batch[edge_center[active_edges]]]
        # new_features = self.bn(new_features)

        if self.latent_resnet:
            update_coefficients = self._latent_resnet_update_params.sigmoid()
            coefficient_old = torch.rsqrt(update_coefficients.square() + 1)
            coefficient_new = update_coefficients * coefficient_old
            features = coefficient_new * new_features + coefficient_old * self.linear_res(features)
        else:
            features = new_features

        # whether it is the last layer
            
        latent_inputs_to_cat = [
            latents[active_edges],
            scalars,
        ]
        
        new_latents = self.latents(torch.cat(latent_inputs_to_cat, dim=-1))
        new_latents = cutoff_coeffs[active_edges].unsqueeze(-1) * new_latents
        # At init, we assume new and old to be approximately uncorrelated
        # Thus their variances add
        # we always want the latent space to be normalized to variance = 1.0,
        # because it is critical for learnability. Still, we want to preserve
        # the _relative_ magnitudes of the current latent and the residual update
        # to be controled by `this_layer_update_coeff`
        # Solving the simple system for the two coefficients:
        #   a^2 + b^2 = 1  (variances add)   &    a * this_layer_update_coeff = b
        # gives
        #   a = 1 / sqrt(1 + this_layer_update_coeff^2)  &  b = this_layer_update_coeff / sqrt(1 + this_layer_update_coeff^2)
        # rsqrt is reciprocal sqrt

        if self.latent_resnet:
            update_coefficients = self._latent_resnet_update_params.sigmoid()
            coefficient_old = torch.rsqrt(update_coefficients.square() + 1)
            coefficient_new = update_coefficients * coefficient_old
            latents = torch.index_add(
                coefficient_old * latents,
                0,
                active_edges,
                coefficient_new * new_latents,
            )

        else:
            latents = torch.index_copy(latents, 0, active_edges, new_latents)

        if self.last_layer:
            node_weights = self.node_embed_mlps(latents[active_edges])
            
            node_features = scatter(
                self._node_weighter(
                    features,
                    node_weights,
                    ),
                edge_center[active_edges],
                dim=0,
            )

            node_features = node_features * norm_const
            edge_weights = self.edge_embed_mlps(latents[active_edges])

            # the features's inclusion of the radial weight here is the only place
            # where features are weighted according to the radial distance
            features = self.tp_out(
                torch.cat(
                    [
                        features,
                        local_env_per_edge[edge_center[active_edges]],
                        local_env_per_edge[edge_neighbor[active_edges]],
                    ], dim=-1
                ),
                edge_vector[active_edges],
            )

            features = self._edge_weighter(
                features,
                edge_weights,
            )

            return node_features, features, cutoff_coeffs, active_edges
        else:
            return latents, features, cutoff_coeffs, active_edges
    