# LSP for Hydra config files

## How to use

To try it out, use the following code snippet in neovim.

```lua

local lspconfig = require("lspconfig")
local configs = require("lspconfig.configs")

local on_attach = function(client, bufnr)
    local nmap = function(keys, func, desc)
        desc = "LSP: " .. desc
        vim.keymap.set("n", keys, func, { buffer = bufnr, desc = desc, noremap = true })
    end

    nmap("gd", vim.lsp.buf.definition, "[G]oto [D]efinition")
    nmap("gD", vim.lsp.buf.declaration, "[G]oto [D]eclaration")
    nmap("gr", require("telescope.builtin").lsp_references, "[G]oto [R]eferences")
    nmap("gI", vim.lsp.buf.implementation, "[G]oto [I]mplementation")
    nmap("K", vim.lsp.buf.hover, "Hover Documentation")
    nmap("<C-k>", vim.lsp.buf.signature_help, "Signature Documentation")

    nmap("<leader>rn", vim.lsp.buf.rename, "[R]e[n]ame")
    nmap("<leader>ca", vim.lsp.buf.code_action, "[C]ode [A]ction")
end

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

- [x] Setup lsprotocol and pygls, see how it works
- [x] Basic skeleton
- [x] Go through hydra documentation and double check its features
- [x] Parse a single yaml (do not account for inheritance)
- [x] Inheritance support
- [ ] Try out the tree-sitter for parsing yaml 
- [ ] Keep the current file's tree (given the inheritance) and more global context (for references etc.)
- [ ] Test main components
- [ ] Unify naming (instead of 'hydra-lsp', 'hydralsp' and 'hydra_lsp')
- [ ] Check if hydra is installed in the current venv before starting up

#### Set of features to implement

- [x] Look-up variable value and possibly doc-string
- [x] Go to the definition of a variable
- [x] Go to references of a variable
- [x] Unroll the hydra file into the resulting config given inheritance and variables
- [x] Autocomplete variable name [Autocomplete]
- [ ] Custom commands to show unrolled config fields [Custom]
- [ ] Check the validity of variables names [Diagnostics]
- [ ] Go to the definition of a variable [Python]
- [ ] Some kind mypy extensions to check types and possible runtime errors [Python]
