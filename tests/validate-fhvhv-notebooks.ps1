$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $PSScriptRoot
$partAPath = Join-Path $root 'notebooks/BigData_FHVHV_Part_A_Processing.ipynb'
$partBPath = Join-Path $root 'notebooks/BigData_FHVHV_Part_B_ML.ipynb'

function Get-NotebookText([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Notebook is missing: $Path"
    }
    $notebook = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json
    return (($notebook.cells | ForEach-Object { $_.source -join '' }) -join "`n")
}

function Assert-Contains([string]$Text, [string]$Needle, [string]$Name) {
    if (-not $Text.Contains($Needle)) { throw "$Name must contain: $Needle" }
}

function Assert-NotContains([string]$Text, [string]$Needle, [string]$Name) {
    if ($Text.Contains($Needle)) { throw "$Name must not contain: $Needle" }
}

$partA = Get-NotebookText $partAPath
$partB = Get-NotebookText $partBPath

Assert-Contains $partA 'spark://spark-master:7077' 'Part A'
Assert-Contains $partA 's3a://bronze/fhvhv/2025/fhvhv_tripdata_2025.parquet' 'Part A'
Assert-Contains $partA 'df = spark.read.parquet(DATA_PATH)' 'Part A'
Assert-Contains $partA 'PROCESSED_DATA_PATH' 'Part A'
Assert-Contains $partA '[PROCESSING]' 'Part A'
Assert-Contains $partA 'Worker distribution verification' 'Part A'
Assert-Contains $partA 'logging' 'Part A'

Assert-Contains $partB 'spark://spark-master:7077' 'Part B'
Assert-Contains $partB 'PROCESSED_DATA_PATH' 'Part B'
Assert-Contains $partB 'trip_time' 'Part B'
Assert-Contains $partB 'RandomForestRegressor' 'Part B'
Assert-Contains $partB 'GBTRegressor' 'Part B'
Assert-Contains $partB 'LinearRegression' 'Part B'
Assert-Contains $partB 'RegressionEvaluator' 'Part B'
Assert-Contains $partB 'logging' 'Part B'

foreach ($item in @($partA, $partB)) {
    foreach ($forbidden in @('hdfs://', 'spark.read.csv', 'toPandas(', 'sklearn', 'RandomForestClassifier', 'GBTClassifier', 'LogisticRegression')) {
        Assert-NotContains $item $forbidden 'Notebook'
    }
}

Assert-NotContains $partB 'dropoff_datetime' 'Part B features'
Write-Output 'FHVHV notebook static audit passed.'
