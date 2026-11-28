# IS2 paper build

The KMITL AI4BA short paper builds from the Markdown drafts with the `kmitl-is-paper` skill. Run from this directory on Windows with Microsoft Word. Build in a scratch directory before copying the verified files to the delivery folder.

```powershell
$kit = Join-Path $env:USERPROFILE '.claude/skills/kmitl-is-paper/scripts'
$stage = Join-Path $env:TEMP ('is2-build-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
foreach ($edition in 'TH', 'EN') {
    $docx = Join-Path $stage "IS2-MWD-$edition.docx"
    $pdf = [IO.Path]::ChangeExtension($docx, '.pdf')
    python "$kit/make_paper.py" --content "content_$($edition.ToLowerInvariant()).py" --figdir ../figures --out $docx
    if ($LASTEXITCODE) { throw "Build failed for $edition" }
    python link_revision_refs.py "../IS2-DRAFT-$edition.md" $docx
    if ($LASTEXITCODE) { throw "Hyperlink and footnote pass failed for $edition" }
    powershell -NoProfile -ExecutionPolicy Bypass -File "$kit/render.ps1" $docx $pdf
    if ($LASTEXITCODE) { throw "PDF export failed for $edition" }
}
```

`md2content.py` converts the drafts into the paperkit content contract. External citations use compact labels or DOIs. The postprocessor inserts hyperlinks, keeps reference entries together and wraps the first Thai affiliation before the institute name. Inspect the final Word exports for the 8–10 page limit and for short line endings throughout, including footnotes and references.
