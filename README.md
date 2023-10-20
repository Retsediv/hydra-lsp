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
- [ ] Go through hydra documentation and double check its features
- [ ] Parse a single yaml (do not account for inheritance)
- [ ] Inheritance support
- [ ] Unify naming (instead of 'hydra-lsp', 'hydralsp' and 'hydra_lsp')
- [ ] ...

#### Set of features to implement

- [x] Look-up variable value and possibly doc-string
- [ ] Check the validity of variables names
- [ ] Autocomplete variable name
- [ ] Go to references of a variable
- [ ] Go to the definition of a variable
- [ ] Unroll the hydra file into the resulting config given inheritance and variables
- [ ] [python] Go to the definition of a variable
- [ ] [python] some kind mypy extensions to check types and possible runtime errors
