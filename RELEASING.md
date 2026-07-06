# Releasing & making the repo citable (Zenodo DOI)

A DOI turns this repo into a citable research artifact — a strong signal on a CV/LinkedIn.

## One-time setup
1. Sign in at <https://zenodo.org> with your GitHub account.
2. Go to **Zenodo → Settings → GitHub**, find `Pr0spektor/climate-risk-early-warning`, and flip
   the switch **On**. (Zenodo now watches the repo for new releases.)

## Mint the DOI
3. On GitHub: **Releases → Draft a new release** → tag `v1.1.0`, title "EW4All CRVA toolkit v1.1.0",
   publish. Zenodo automatically archives the release and issues a DOI.
4. Copy the **DOI badge** Zenodo shows and paste it at the top of `README.md`, replacing the
   placeholder:

   ```
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
   ```

5. (Optional) add the DOI to `CITATION.cff` as `doi:` and to your LinkedIn "Featured" / CV.

## Versioning
Zenodo issues a *concept DOI* (always latest) plus a per-version DOI. Cite the concept DOI on your
CV so it never goes stale.
