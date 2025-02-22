<#
This deals with the default execution policy restrictions associated with running PowerShell scripts.
Failure to do so with result in errors.

Need to run this before: Set-ExecutionPolicy RemoteSigned
Then when we're done: Set-ExecutionPolicy Restricted
#>

$nocomment = [reflection.assembly]::LoadWithPartialName("System.Drawing")
get-childitem *.jpg | foreach {
    #$_.Name
    # Get the metadata from the full filename
    $pic = New-Object System.Drawing.Bitmap($_.fullname)
    # https://nicholasarmstrong.com/2010/02/exif-quick-reference/
    [string] $dateTakenString = [System.Text.Encoding]::ASCII.GetString($pic.GetPropertyItem(36867).Value)
    
    # Try to get the cameraModel; if that fails try checking the makernotes
    [string] $cameraModel = ""
    try {
        $cameraModel = [System.Text.Encoding]::ASCII.GetString($pic.GetPropertyItem(272).Value)
    }
    catch {
        try {
            [String] $makerNoteString = [System.Text.Encoding]::ASCII.GetString($pic.GetPropertyItem(37500).Value)
            [String] $makerNoteSubString = $makerNoteString.Substring(10,10)
            [String] $GoProMakerNoteSubString = "LAJ8052936"
            if ($makerNoteSubString -eq $GoProMakerNoteSubString) {
                $cameraModel = "HERO7 Black"
            }
        }
        catch { echo("Failed to get makernote") }
    }

    # Grab the date, then dump it into the "sortable" format so that we can replace the Timezone and : character
    $date = [datetime]::ParseExact($dateTakenString,"yyyy:MM:dd HH:mm:ss`0",$Null)

    # Change the date because the GoPro was off
    <#
    $date = $date.AddYears(0)
    $date = $date.AddMonths(0)
    $date = $date.AddDays(0)
    $date = $date.AddHours(0)
    $date = $date.AddMinutes(0)
    #>
    if (($cameraModel -eq "iPhone 13 Pro") -or ($cameraModel -eq "iPhone 15 Pro")){
        <#
        $date = $date.AddHours(-7)
        #>
    } elseif ($cameraModel -eq "HERO7 Black"){
        $date = $date.AddYears(4)
        $date = $date.AddMonths(8)
        $date = $date.AddDays(8)
        $date = $date.AddHours(-8)
        $date = $date.AddMinutes(20)
    } else {
        #continue
    }

    [string] $newfilenameroot = get-date $date -format s
    $newfilenameroot = $newfilenameroot.Replace("T", " ")
    $newfilenameroot = $newfilenameroot.Replace(":", ".")
    # We're keeping $newfilenameroot so that we can append -1 if needed
    [string] $newfilename = $newfilenameroot + ".jpg"

    # Dispose of the image object, do the rename, then spit out the new file name
    $pic.Dispose()
    # Only rename if the file name changed
    if ($_.Name -eq $newfilename) {
        echo ($_.Name + " == Not renaming")
    }
    else {
        # If a file with the same name already exists, loop through and append a number to the end until it doesn't
        if (Test-Path -Path $newfilename -PathType Leaf) {
            [int] $fileNameIndex = 0
            Do {
                $fileNameIndex++
                [string] $filenameincremented = $newfilenameroot + "-" + $fileNameIndex + ".jpg"
            } Until (
                ($fileNameIndex -eq 100)`
                -or (-not(Test-Path -Path $filenameincremented -PathType Leaf))`
                -or ($_.Name -eq $filenameincremented)
                )

            # Now that we have a unique name overwrite $newfilename
            $newfilename = $filenameincremented
        }

        # Complete the rename
        rename-item $_ $newfilename -Force
        echo ($_.Name + " -> " + $newfilename)
    }
}