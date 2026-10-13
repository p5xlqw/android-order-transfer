$ErrorActionPreference = 'Stop'
    [Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$shell = New-Object -ComObject Shell.Application
$foldersById = @{}
$folderMetaById = @{}
$nextId = 1

function Send-Json($value) {
    [Console]::Out.WriteLine((ConvertTo-Json -InputObject $value -Depth 8 -Compress))
    [Console]::Out.Flush()
}

function Scan-Folders {
    $script:foldersById = @{}
    $script:folderMetaById = @{}
    $script:folderRows = New-Object 'System.Collections.Generic.List[object]'
    $script:nextId = 1
    try {
        $computer = $shell.Namespace(17)
        foreach ($deviceItem in $computer.Items()) {
            try {
                if (-not $deviceItem.IsFolder) { continue }
                if ($deviceItem.IsFileSystem) { continue }
                $deviceFolder = $deviceItem.GetFolder
                if ($null -eq $deviceFolder) { continue }
                $id = $script:nextId
                $script:nextId++
                $name = [string]$deviceItem.Name
                $script:foldersById[$id] = $deviceFolder
                $script:folderMetaById[$id] = @{ device = $name; path = $name; depth = 0 }
                $script:folderRows.Add([pscustomobject]@{
                    id = $id; parentId = -1; depth = 0; name = $name
                    path = $name; device = $name; isDevice = $true
                })
            } catch { }
        }
        Send-Json @{ type = 'tree'; folders = $script:folderRows.ToArray() }
    } catch {
        Send-Json @{ type = 'scan_error'; message = $_.Exception.Message }
    }
}

function Get-ChildFolders([int]$parentId) {
    try {
        $parentFolder = $script:foldersById[$parentId]
        $parentMeta = $script:folderMetaById[$parentId]
        if ($null -eq $parentFolder -or $null -eq $parentMeta) { throw 'フォルダ情報を取得できません。端末を再検索してください。' }
        $rows = New-Object 'System.Collections.Generic.List[object]'
        foreach ($item in $parentFolder.Items()) {
            try {
                if (-not $item.IsFolder) { continue }
                $childFolder = $item.GetFolder
                if ($null -eq $childFolder) { continue }
                $id = $script:nextId
                $script:nextId++
                $name = [string]$item.Name
                $path = "$($parentMeta.path)\$name"
                $script:foldersById[$id] = $childFolder
                $script:folderMetaById[$id] = @{ device = $parentMeta.device; path = $path; depth = ($parentMeta.depth + 1) }
                $rows.Add([pscustomobject]@{
                    id = $id; parentId = $parentId; depth = ($parentMeta.depth + 1)
                    name = $name; path = $path; device = $parentMeta.device; isDevice = $false
                })
            } catch { }
        }
        Send-Json @{ type = 'children'; parentId = $parentId; folders = $rows.ToArray() }
    } catch {
        Send-Json @{ type = 'children_error'; parentId = $parentId; message = $_.Exception.Message }
    }
}

function Test-DeviceItemMatchesFile($item, [string]$fileName) {
    $expectedName = [IO.Path]::GetFileName($fileName)
    $expectedStem = [IO.Path]::GetFileNameWithoutExtension($expectedName)
    $expectedExtension = [IO.Path]::GetExtension($expectedName)
    $itemName = [string]$item.Name
    if ([string]::Equals($itemName, $expectedName, [StringComparison]::OrdinalIgnoreCase)) { return $true }

    try {
        $propertyName = [string]$item.ExtendedProperty('System.FileName')
        if ([string]::Equals($propertyName, $expectedName, [StringComparison]::OrdinalIgnoreCase)) { return $true }
        $propertyExtension = [string]$item.ExtendedProperty('System.FileExtension')
        if ([string]::Equals($itemName, $expectedStem, [StringComparison]::OrdinalIgnoreCase) -and
            [string]::Equals($propertyExtension, $expectedExtension, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    } catch { }

    # MTP Shell items may omit the extension from Name; Path and Type retain it.
    $itemPath = [string]$item.Path
    if ($itemPath) {
        $pathLeaf = [IO.Path]::GetFileName($itemPath.TrimEnd('\'))
        if ([string]::Equals($pathLeaf, $expectedName, [StringComparison]::OrdinalIgnoreCase)) { return $true }
    }
    if (-not [string]::Equals($itemName, $expectedStem, [StringComparison]::OrdinalIgnoreCase)) { return $false }

    $type = [string]$item.Type
    $extensionName = $expectedExtension.TrimStart('.').ToUpperInvariant()
    if ($type -match [regex]::Escape($extensionName)) { return $true }
    if ($expectedExtension -in @('.jpg', '.jpeg') -and $type -match 'JPG|JPEG') { return $true }
    if ($expectedExtension -eq '.wav' -and $type -match 'WAVE|WAV') { return $true }
    return $false
}

function Find-ChildItem($folder, [string]$name) {
    foreach ($item in $folder.Items()) {
        if (Test-DeviceItemMatchesFile $item $name) { return $item }
    }
    return $null
}

function Get-MtpRelativeFolder($baseFolder, [string]$relativePath, [bool]$create) {
    $current = $baseFolder
    if ([string]::IsNullOrWhiteSpace($relativePath)) { return $current }
    $segments = $relativePath.Replace('\', '/').Split('/', [StringSplitOptions]::RemoveEmptyEntries)
    foreach ($segment in $segments) {
        if ($segment -in @('.', '..') -or $segment -match '[\\/:*?"<>|]' -or $segment -match '[. ]$') {
            throw "展開先のフォルダ名が安全でないため停止しました: $segment"
        }
        $child = $null
        foreach ($item in @($current.Items())) {
            if ([string]::Equals([string]$item.Name, $segment, [StringComparison]::OrdinalIgnoreCase)) {
                if (-not $item.IsFolder) { throw "展開先に同名のファイルがあり、フォルダを作成できません: $segment" }
                $child = $item.GetFolder
                break
            }
        }
        if ($null -eq $child -and -not $create) { return $null }
        if ($null -eq $child) {
            [void]$current.NewFolder($segment)
            foreach ($item in @($current.Items())) {
                if ($item.IsFolder -and [string]::Equals([string]$item.Name, $segment, [StringComparison]::OrdinalIgnoreCase)) {
                    $child = $item.GetFolder
                    break
                }
            }
            if ($null -eq $child) { throw "端末にフォルダを作成できませんでした: $segment" }
        }
        $current = $child
    }
    return $current
}

function Get-DeviceItemSize($folder, $item) {
    try {
        $size = [long]$item.Size
        if ($size -gt 0) { return $size }
    } catch { }
    try {
        $size = [long]$item.ExtendedProperty('System.Size')
        if ($size -gt 0) { return $size }
    } catch { }
    try {
        $detail = [string]$folder.GetDetailsOf($item, 1)
        if ($detail -match '([\d,]+(?:\.\d+)?)\s*(B|KB|MB|GB|TB|バイト|キロバイト|メガバイト|ギガバイト)') {
            $amount = [double]::Parse($Matches[1].Replace(',', ''), [Globalization.CultureInfo]::InvariantCulture)
            $unit = $Matches[2].ToUpperInvariant()
            $factor = switch -Regex ($unit) {
                '^(B|バイト)$' { 1; break }
                '^(KB|キロバイト)$' { 1KB; break }
                '^(MB|メガバイト)$' { 1MB; break }
                '^(GB|ギガバイト)$' { 1GB; break }
                '^(TB)$' { 1TB; break }
                default { 1 }
            }
            return [long]($amount * $factor)
        }
    } catch { }
    return -1L
}

function Get-SourceMetadata($request) {
    $propertyMap = [ordered]@{
        'トラック番号' = 'System.Media.TrackNumber'
        'ディスク番号' = 'System.Media.DiscNumber'
        'タイトル' = 'System.Title'
        'アルバム' = 'System.Media.AlbumTitle'
        'アーティスト' = 'System.Media.Artist'
        'ジャンル' = 'System.Media.Genre'
        '作曲者' = 'System.Media.Composer'
        '年' = 'System.Media.Year'
        '再生時間' = 'System.Media.Duration'
        'ビットレート' = 'System.Audio.EncodingBitrate'
        'サンプルレート' = 'System.Audio.SampleRate'
        '撮影日時' = 'System.Photo.DateTaken'
        'カメラ' = 'System.Photo.CameraModel'
        '画像サイズ' = 'System.Image.Dimensions'
        '画像の幅' = 'System.Image.HorizontalSize'
        '画像の高さ' = 'System.Image.VerticalSize'
        'ページ数' = 'System.Document.PageCount'
    }
    try {
        $results = New-Object 'System.Collections.Generic.List[object]'
        foreach ($source in @($request.files)) {
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PC側のファイルが見つかりません: $source" }
            $fullPath = [IO.Path]::GetFullPath([string]$source)
            $folder = $shell.Namespace([IO.Path]::GetDirectoryName($fullPath))
            $item = $folder.ParseName([IO.Path]::GetFileName($fullPath))
            $metadata = [ordered]@{}
            if ($null -ne $item) {
                foreach ($label in $propertyMap.Keys) {
                    try {
                        $value = $item.ExtendedProperty($propertyMap[$label])
                        if ($null -ne $value -and [string]$value -ne '') {
                            if ($value -is [DateTime]) { $metadata[$label] = $value.ToString('o') }
                            elseif ($value -is [Array]) { $metadata[$label] = ($value -join ', ') }
                            else { $metadata[$label] = [string]$value }
                        }
                    } catch { }
                }
            }
            $results.Add([pscustomobject]@{ path = $fullPath; metadata = $metadata })
        }
        Send-Json @{ type = 'source_metadata'; requestId = $request.requestId; files = $results.ToArray() }
    } catch {
        Send-Json @{ type = 'source_metadata'; requestId = $request.requestId; files = @(); message = $_.Exception.Message }
    }
}

function Get-TransferPreflight($request) {
    try {
        $target = $script:foldersById[[int]$request.targetId]
        if ($null -eq $target) { throw '転送先フォルダを再取得できません。端末を再検索してください。' }
        $files = @($request.files)
        $relativePaths = @($request.relativePaths)
        $createFolderName = [string]$request.createFolderName
        if ($createFolderName) {
            if ($createFolderName -in @('.', '..') -or $createFolderName -match '[\\/:*?"<>|]' -or $createFolderName -match '[. ]$') {
                throw 'フォルダ名に使用できない文字が含まれています。'
            }
            foreach ($item in @($target.Items())) {
                if ([string]::Equals([string]$item.Name, $createFolderName, [StringComparison]::OrdinalIgnoreCase)) {
                    throw "転送先に同じ名前の項目があります: $createFolderName`n別の名前を指定してください。"
                }
            }
            foreach ($source in $files) {
                if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PC側のファイルが見つかりません: $source" }
            }
            $totalBytes = 0L
            foreach ($source in $files) { $totalBytes += (Get-Item -LiteralPath $source).Length }
            Send-Json @{ type = 'preflight_done'; ok = $true; total = $files.Count
                totalBytes = $totalBytes; conflicts = @() }
            return
        }
        $conflicts = New-Object 'System.Collections.Generic.List[string]'
        $totalBytes = 0L
        for ($fileIndex = 0; $fileIndex -lt $files.Count; $fileIndex++) {
            $source = $files[$fileIndex]
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PC側のファイルが見つかりません: $source" }
            $totalBytes += (Get-Item -LiteralPath $source).Length
            $relativePath = if ($fileIndex -lt $relativePaths.Count) { [string]$relativePaths[$fileIndex] } else { '' }
            $destinationFolder = Get-MtpRelativeFolder $target $relativePath $false
            if ($null -eq $destinationFolder) { continue }
            $name = [IO.Path]::GetFileName($source)
            foreach ($existingItem in @($destinationFolder.Items())) {
                if (Test-DeviceItemMatchesFile $existingItem $name) {
                    $conflictName = $name
                    if ($relativePath) { $conflictName = "$relativePath/$name" }
                    $conflicts.Add($conflictName)
                    break
                }
            }
        }
        Send-Json @{ type = 'preflight_done'; ok = $true; total = $files.Count
            totalBytes = $totalBytes; conflicts = $conflicts.ToArray() }
    } catch {
        Send-Json @{ type = 'preflight_done'; ok = $false; message = $_.Exception.Message }
    }
}

function Transfer-Files($request) {
    $completed = 0
    $files = @($request.files)
        $relativePaths = @($request.relativePaths)
    $total = $files.Count
    $cancelFile = [string]$request.cancelFile
    $cancelled = $false
    $skipped = 0
    $currentIndex = 0
    $currentName = ''
    $totalBytes = 0L
    $processedBytes = 0L
    try {
        $target = $script:foldersById[[int]$request.targetId]
        if ($null -eq $target) { throw '転送先フォルダを再取得できません。端末を再検索してください。' }
        $createFolderName = [string]$request.createFolderName
        if ($createFolderName) {
            if ($createFolderName -in @('.', '..') -or $createFolderName -match '[\\/:*?"<>|]' -or $createFolderName -match '[. ]$') {
                throw 'フォルダ名に使用できない文字が含まれています。'
            }
            foreach ($item in @($target.Items())) {
                if ([string]::Equals([string]$item.Name, $createFolderName, [StringComparison]::OrdinalIgnoreCase)) {
                    throw "転送先に同じ名前の項目があります: $createFolderName"
                }
            }
            [void]$target.NewFolder($createFolderName)
            $createdFolder = $null
            foreach ($item in $target.Items()) {
                if ($item.IsFolder -and [string]::Equals([string]$item.Name, $createFolderName, [StringComparison]::OrdinalIgnoreCase)) {
                    $createdFolder = $item.GetFolder
                    break
                }
            }
            if ($null -eq $createdFolder) { throw "新しいフォルダを端末で確認できませんでした: $createFolderName" }
            $target = $createdFolder
        }
        $skipNames = @{}
        for ($fileIndex = 0; $fileIndex -lt $files.Count; $fileIndex++) {
            $source = $files[$fileIndex]
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) { throw "PC側のファイルが見つかりません: $source" }
            $totalBytes += (Get-Item -LiteralPath $source).Length
            $relativePath = if ($fileIndex -lt $relativePaths.Count) { [string]$relativePaths[$fileIndex] } else { '' }
            $destinationFolder = Get-MtpRelativeFolder $target $relativePath $false
            if ($null -eq $destinationFolder) { continue }
            $name = [IO.Path]::GetFileName($source)
            $match = $null
            foreach ($existingItem in @($destinationFolder.Items())) {
                if (Test-DeviceItemMatchesFile $existingItem $name) {
                    $match = $existingItem
                    break
                }
            }
            if ($null -ne $match) {
                $skipKey = "$relativePath|$name"
                if ($request.skipExisting) { $skipNames[$skipKey] = $true }
                else { throw "転送先に同名ファイルがあります: $name`n既存ファイルを上書きせず、ここで停止しました。" }
            }
        }
        $index = 0
        foreach ($source in $files) {
            if ($cancelFile -and (Test-Path -LiteralPath $cancelFile)) {
                $cancelled = $true
                break
            }
            $index++
            $name = [IO.Path]::GetFileName($source)
            $currentIndex = $index
            $currentName = $name
            $relativePath = if ($index -le $relativePaths.Count) { [string]$relativePaths[$index - 1] } else { '' }
            $skipKey = "$relativePath|$name"
            if ($skipNames.ContainsKey($skipKey)) {
                $skipped++
                $processedBytes += (Get-Item -LiteralPath $source).Length
                Send-Json @{ type = 'skipped'; index = $index; total = $total; name = $name; bytesDone = $processedBytes; bytesTotal = $totalBytes }
                continue
            }
            $destinationFolder = Get-MtpRelativeFolder $target $relativePath $true
            $expected = (Get-Item -LiteralPath $source).Length
            if ($cancelFile -and (Test-Path -LiteralPath $cancelFile)) {
                $cancelled = $true
                break
            }
            Send-Json @{ type = 'progress'; index = $index; total = $total; name = $name }
            Send-Json @{ type = 'phase'; message = "端末へ転送を依頼中: $name" }
            # Keep Shell/MTP failures from opening modal Windows error dialogs.
            # FOF_SILENT | FOF_NOCONFIRMATION | FOF_NOERRORUI.
            $destinationFolder.CopyHere($source, 0x414)
            Send-Json @{ type = 'phase'; message = "端末側の転送完了を確認中: $name" }
            $maxDuration = [Math]::Min(3600, [Math]::Max(300, 300 + [Math]::Ceiling($expected / 131072)))
            $deadline = [DateTime]::UtcNow.AddSeconds($maxDuration)
            $seen = $false
            $lastSize = -1L
            $largestObservedSize = -1L
            $lastSizeProgressAt = [DateTime]::UtcNow
            $stableCount = 0
            $cancelNoticeSent = $false
            $lastHeartbeatAt = [DateTime]::UtcNow
            while ([DateTime]::UtcNow -lt $deadline) {
                Start-Sleep -Milliseconds 350
                if (([DateTime]::UtcNow - $lastHeartbeatAt).TotalSeconds -ge 5) {
                    Send-Json @{ type = 'heartbeat'; index = $index; name = $name }
                    $lastHeartbeatAt = [DateTime]::UtcNow
                }
                if ($cancelFile -and (Test-Path -LiteralPath $cancelFile) -and -not $cancelNoticeSent) {
                    Send-Json @{ type = 'cancel_wait'; name = $name }
                    $cancelNoticeSent = $true
                }
                $created = Find-ChildItem $destinationFolder $name
                if ($null -ne $created -and $created.IsFolder) { $created = $null }
                if ($null -eq $created) { continue }
                $seen = $true
                $size = Get-DeviceItemSize $destinationFolder $created
                if ($size -gt $largestObservedSize) {
                    $largestObservedSize = $size
                    $lastSizeProgressAt = [DateTime]::UtcNow
                }
                if ($size -gt 0 -and $expected -gt 0 -and $totalBytes -gt 0) {
                    $currentBytes = [Math]::Min([long]$expected, [long]$size)
                    Send-Json @{ type = 'file_progress'; index = $index; total = $total; name = $name
                        currentBytes = $currentBytes; currentTotal = $expected
                        bytesDone = ($processedBytes + $currentBytes); bytesTotal = $totalBytes }
                }
                if ($expected -eq 0) {
                    if ($size -le 0) { $stableCount++ } else { $stableCount = 0 }
                } elseif ($size -lt 0) {
                    # MTP occasionally stops exposing Size after reporting the complete file.
                    # Keep the last confirmed size during the short stability window.
                    if ($lastSize -ge ($expected - 1024)) { $stableCount++ }
                } elseif ($size -ge ($expected - 1024)) {
                    if ($size -eq $lastSize) { $stableCount++ } else { $stableCount = 0 }
                    $lastSize = $size
                } else {
                    $stableCount = 0
                    $lastSize = $size
                }
                if ($stableCount -ge 6) { break }
                if (([DateTime]::UtcNow - $lastSizeProgressAt).TotalSeconds -ge 90) { break }
            }
            if (-not $seen) { throw "端末にファイルが現れませんでした: $name" }
            if ($stableCount -lt 6) {
                if ($cancelNoticeSent) {
                    throw "中止要求を受け付けましたが、現在のファイルの完了を確認できませんでした: $name`n端末側に不完全なファイルが残っていないか確認してください。"
                }
                throw "転送完了を確認できませんでした: $name`n端末側にファイルが作成済みの可能性があります。状態を確認してください。"
            }
            $completed++
            $processedBytes += $expected
            Send-Json @{ type = 'file_done'; index = $index; total = $total; name = $name
                bytesDone = $processedBytes; bytesTotal = $totalBytes }
        }
        if ($cancelFile -and (Test-Path -LiteralPath $cancelFile)) { $cancelled = $true }
        if ($cancelled) {
            Send-Json @{ type = 'transfer_done'; ok = $false; cancelled = $true; total = $total; completed = $completed; skipped = $skipped; message = "中止しました。現在のファイルは完了確認後に停止し、次のファイルは転送していません。" }
        } else {
            Send-Json @{ type = 'transfer_done'; ok = $true; total = $total; completed = $completed; skipped = $skipped }
        }
    } catch {
        Send-Json @{ type = 'transfer_done'; ok = $false; total = $total; completed = $completed;
            failedIndex = $currentIndex; failedName = $currentName; message = $_.Exception.Message }
    }
}

Scan-Folders
while ($true) {
    $line = [Console]::In.ReadLine()
    if ($null -eq $line) { break }
    try {
        $request = ConvertFrom-Json -InputObject $line
        switch ($request.action) {
            'scan' { Scan-Folders }
            'children' { Get-ChildFolders ([int]$request.id) }
            'source_metadata' { Get-SourceMetadata $request }
            'preflight' { Get-TransferPreflight $request }
            'transfer' { Transfer-Files $request }
            'quit' { exit }
            default { Send-Json @{ type = 'error'; message = '不明な操作です。' } }
        }
    } catch {
        Send-Json @{ type = 'error'; message = $_.Exception.Message }
    }
}
