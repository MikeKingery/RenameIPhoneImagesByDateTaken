<#
This deals with the default execution policy restrictions associated with running PowerShell scripts.
Failure to do so with result in errors.

Need to run this before: Set-ExecutionPolicy RemoteSigned
Then when we're done: Set-ExecutionPolicy Restricted
#>
 
# This function returns a dictionary of all the metadata we can find
function getFileAttributes ([string[]]$filePath){
    $shell = New-Object -COMObject Shell.Application
    $shellFolder = $shell.Namespace($(split-path $filePath))
    $shellFile = $shellFolder.ParseName($(split-path $filePath -leaf))
    $attributes = @{}
    0..308 | ForEach-Object {
        $propertyName = $shellFolder.GetDetailsOf($shellFolder, $_)
        $propertyValue = $shellFolder.GetDetailsOf($shellFile, $_)
        #if ($propertyValue){ write-host "-- $propertyName`: $propertyValue" }
        if($propertyName -ne '' -and $null -ne $propertyName){
            $attributes[$propertyName] = $propertyValue
        }
    }
    $shell=$null
    return $attributes
}

# Loop through all of the video files and rename
Get-ChildItem .\* -Include "*.mp4", "*.avi", "*.mkv", "*.mov", "*.wmv" | ForEach-Object {
    $filePath=$_.FullName
    $fileName=$_.Name
    $fileExtension = $_.Extension
    
    #Write-Host "##################################################################################################"
    #Write-Host $fileName

    # We want to get a bunch of dates from the file and use which ever one is older for the date created
    # Start by trying to grab the CreationTime right from the file
    $CreationTime = $_.CreationTime -creplace '\P{IsBasicLatin}'

    # Now let's do some metadata collection to grab from the file attributes and put it into a dictionary we can reference
    $fileAttributeDictionary = getFileAttributes($filePath)
    $DateTaken = $fileAttributeDictionary['Date taken'] -creplace '\P{IsBasicLatin}'
    $MediaCreated = $fileAttributeDictionary['Media created'] -creplace '\P{IsBasicLatin}'
    $DateModified = $fileAttributeDictionary['Date modified'] -creplace '\P{IsBasicLatin}'
    $DateCreated = $fileAttributeDictionary['Date created'] -creplace '\P{IsBasicLatin}'
    
    <#
    Write-Host "    CreationTime = $($CreationTime)"
    Write-Host "    DateTaken = $($DateTaken)"
    Write-Host "    MediaCreated = $($MediaCreated)"
    Write-Host "    DateModified = $($DateModified)"
    Write-Host "    DateCreated = $($DateCreated)"
    #>

    # Now that we have all of the dates, find the one which is the oldest and use it
    $dateArray = @(
        $CreationTime,
        $DateTaken,
        $MediaCreated,
        $DateModified,
        $DateCreated
    )

    $dateTimes = $dateArray | ForEach-Object { if ($_){ Get-Date $_ } }
    $date = ($dateTimes | Sort-Object)[0]
    #Write-Host "The oldest date is: $($date)"

    try {
        # Change the date because the GoPro was off
        <#
        $date = $date.AddHours(6)
        $date = $date.AddYears(7)
        $date = $date.AddMonths(-6)
        $date = $date.AddDays(-20)
        #>
        $date = $date.AddHours(-7)

        [string] $newfilenameroot = get-date $date -format s
        $newfilenameroot = $newfilenameroot.Replace("T", " ")
        $newfilenameroot = $newfilenameroot.Replace(":", ".")
        # We're keeping $newfilenameroot so that we can append -1 if needed
        [string] $newfilename = $newfilenameroot + $fileExtension

        # Do the rename, then spit out the new file name
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
                    [string] $filenameincremented = $newfilenameroot + "-" + $fileNameIndex + $fileExtension
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
    catch {
        # If we fail, stop
        throw
        break
    }
}