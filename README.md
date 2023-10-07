# LSP for Hydra config files

## How to use

To try it out, use the following code snippet in neovim.

```lua

local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

if not configs.hydralsp then
    configs.hydralsp = {
        default_config = {
            cmd = { "hydra-lsp" },
            root_dir = lspconfig.util.root_pattern(".git"),
            filetypes = { "python" },
        },
    }
end
lspconfig.hydralsp.setup({
    on_attach = lsp.on_attach,
})

```

Note: make sure to install hydra-lsp so that nvim can find an executable (`poetry install`)

#### To-Do

- [ ] Setup lsprotocol and pygls, see how it works
- [ ] Go through hydra documentation and double check its features
- [ ] Parse a single yaml (do not account for inheritance)
- [ ] Inheritance support
- [ ] ...

#### Set of features to implement

- [ ] Look-up variable value and possibly doc-string
- [ ] Go to references of a variable
- [ ] Go to the definition of a variable
- [ ] Unroll the hydra file into the resulting config given inheritance and variables
