# Publishing on GitHub Pages

The project documentation is built with Jupyter Book 2 and published as a
GitHub Pages project site at
`https://<username>.github.io/<repository-name>/`. The site build needs the
repository path as its base URL, supplied through `BASE_URL`.

## Classical deployment with `gh-pages`

From the `docs/` directory, build the site and publish the generated HTML to
the `gh-pages` branch:

```sh
BASE_URL=/ASC-ODE jupyter-book build --html
pip install ghp-import
ghp-import -n -p -f _build/html
```

`ghp-import` copies the HTML files to the `gh-pages` branch and pushes that
branch to GitHub. In the repository settings, select **Settings → Pages →
Build and deployment → Deploy from a branch**, then choose `gh-pages` as the
branch and `/ (root)` as the folder.

In Windows PowerShell, set the base URL before building:

```powershell
$env:BASE_URL = "/ASC-ODE"
jupyter-book build --html
pip install ghp-import
ghp-import -n -p -f _build/html
```

## Publishing with GitHub Actions

GitHub Actions can build and publish the book after each push to `main`. The
ASC-ODE repository already has this workflow in
`.github/workflows/docs.yml`; it also supports manual runs from the Actions
tab. It sets `BASE_URL` from the repository name, builds the HTML strictly,
and deploys the result to GitHub Pages.

Enable Actions in a fork if its workflows are disabled. In **Settings → Pages
→ Build and deployment**, select **GitHub Actions** as the source. After the
next push to `main`, the **Actions** tab shows the “Documentation” workflow.
When it completes, the documentation is available at
`https://<username>.github.io/ASC-ODE/`.

This repository uses the GitHub Actions deployment. For a book in the
repository root, `jupyter-book init --gh-pages` can generate a Pages workflow.
