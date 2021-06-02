<#
This deals with the default execution policy restrictions associated with running PowerShell scripts.
Failure to do so with result in errors.

Need to run this before: Set-ExecutionPolicy RemoteSigned
Then when we're done: Set-ExecutionPolicy Restricted
#>

$nocomment = [reflection.assembly]::LoadWithPartialName("System.Drawing")
get-childitem *.jpg | foreach {
    # $_.Name
    # Get the metadata from the full filename
    $pic = New-Object System.Drawing.Bitmap($_.fullname)
    $bitearr = $pic.GetPropertyItem(36867).Value
    $string = [System.Text.Encoding]::ASCII.GetString($bitearr)

    # Grab the date, then dump it into the "sortable" format so that we can replace the Timezone and : character
    $date = [datetime]::ParseExact($string,"yyyy:MM:dd HH:mm:ss`0",$Null)
    [string] $newfilename = get-date $date -format s
    $newfilename = $newfilename.Replace("T", " ")
    $newfilename = $newfilename.Replace(":", ".")
    $newfilename += ".jpg"

    # Dispose of the image object, do the rename, then spit out the new file name
    $pic.Dispose()
    rename-item $_ $newfilename -Force
    $newfilename
}