# LSP for Hydra config files

![Test Workflow](https://github.com/retsediv/hydra-lsp/actions/workflows/test.yml/badge.svg)
[![PyPi Version](https://badge.fury.io/py/hydra-lsp.svg)](https://pypi.python.org/pypi/hydra-lsp/)  


<p align="center">
  <img src="icon_wide.png" alt="Hydra LSP" width="400"/>
</p>


## Installation

1. Using pypi: `pip install hydra-lsp`

2. Using poetry: `poetry install`

## Features

1. Ignore certain lines - if you do not want to perform diagnostics on specific line, then add `# hydra: skip` to the end of that line

## How to use

To try it out, use the following code snippet in neovim.

Note: If you are VS Code user - check out the [extension](https://github.com/retsediv/hydra-lsp-vscode).

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
            filetypes = { "yaml" },
        },
    }
end

lspconfig.hydralsp.setup({
    on_attach = lsp.on_attach,
})

```

Note: make sure to install hydra-lsp so that nvim can find an executable (`poetry install`)
