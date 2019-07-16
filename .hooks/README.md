# Hooks
## Setup
Ensure that you have **ctags** installed on your machine. 

### Linux
```bash
sudo apt-get install ctags
```
or use whatever package manager you prefer.

### Windows
If you're using **vim**, you're *probably* using a linux terminal of some sort. Either **Cygwin** or **msysgit**

More detailed information can be found on [Stack Exchange](https://superuser.com/a/701175)

---

Optionally, you may install these packages to improve your experience with **ctags**.

[`pathogen.vim`](https://github.com/tpope/vim-pathogen) is a sort of like a package manager. It keeps track of your `'runtimepath'`

[`fugitive.vim`](https://github.com/tpope/vim-fugitive) is a wrapper for Git in Vim.

---

### Git
#### Hooks
If you don't have any existing hooks, you can link the `.hooks` folder to your `.git/hooks` folder. 

```bash
ln -s $PWD/.hooks $PWD/.git/hooks
```

If you do have existing hooks, you will have to manually alter them to run the actions in `.hooks`.

#### Aliasing
You may optionally add a `git ctags` command by running
```bash
git options --global alias.ctags '!.git/hooks/ctags'
```

## Usage
To generate tags, use `git ctags`.

To follow tags in vim, use `<C-]>`.

To backtrack tags in vim, use `<C-t>`.
