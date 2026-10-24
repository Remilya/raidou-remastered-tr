param(
    [string[]]$SourceDirectories = @(
        (Join-Path (Split-Path -Parent $PSScriptRoot) 'Content\JSON'),
        (Join-Path (Split-Path -Parent $PSScriptRoot) 'Content\DLC\JSON')
    ),
    [string]$OutputFile = (Join-Path (Split-Path -Parent $PSScriptRoot) 'Config\JSON_Categories.json')
)

$placeholderValues = @('', 'NULL', 'ER100')

function Test-RealText {
    param([object]$Value)

    if ($null -eq $Value) {
        return $false
    }

    return $placeholderValues -notcontains ([string]$Value).Trim()
}

$dialogueFiles = [System.Collections.Generic.List[string]]::new()
$commonTextFiles = [System.Collections.Generic.List[string]]::new()

$sourceFiles = foreach ($directory in $SourceDirectories) {
    if (Test-Path -LiteralPath $directory) {
        Get-ChildItem -LiteralPath $directory -Recurse -File -Filter '*.json'
    }
}

$duplicateNames = $sourceFiles | Group-Object Name | Where-Object Count -gt 1
if ($duplicateNames) {
    throw "Duplicate JSON filenames found across source directories: $($duplicateNames.Name -join ', ')"
}

foreach ($file in $sourceFiles | Sort-Object Name) {
    $json = Get-Content -LiteralPath $file.FullName -Raw | ConvertFrom-Json
    $entries = @($json._TextMsgData.Array)
    $hasSpeakerDialoguePair = $false

    for ($index = 0; $index -lt ($entries.Count - 1); $index++) {
        $speaker = $entries[$index]
        $dialogue = $entries[$index + 1]

        # Speaker records use the lowercase source key and precede an uppercase text record.
        if (
            $speaker.msgID -cmatch '[a-z]' -and
            $dialogue.msgID -cnotmatch '[a-z]' -and
            (Test-RealText $speaker.msgStr) -and
            (Test-RealText $dialogue.msgStr)
        ) {
            $hasSpeakerDialoguePair = $true
            break
        }
    }

    if ($hasSpeakerDialoguePair) {
        $dialogueFiles.Add($file.Name)
    }
    else {
        $commonTextFiles.Add($file.Name)
    }
}

$result = [ordered]@{
    generatedAt = (Get-Date).ToString('o')
    sourceDirectories = @($SourceDirectories | Where-Object { Test-Path -LiteralPath $_ } | ForEach-Object {
        (Resolve-Path -LiteralPath $_).Path
    })
    rule = 'Dialogue files contain at least one real lowercase-key speaker record immediately followed by a real uppercase-key dialogue record. NULL, ER100, and blank values are ignored. All remaining files are Common Texts.'
    counts = [ordered]@{
        total = $dialogueFiles.Count + $commonTextFiles.Count
        dialogues = $dialogueFiles.Count
        commonTexts = $commonTextFiles.Count
    }
    dialogues = $dialogueFiles
    commonTexts = $commonTextFiles
}

$result | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $OutputFile -Encoding utf8
Write-Output "Categorized $($result.counts.total) files: $($result.counts.dialogues) Dialogues, $($result.counts.commonTexts) Common Texts."
Write-Output "Manifest: $OutputFile"
