const CodeInput = ({
  code,
  language,
  analysisType,
  onCodeChange,
  onLanguageChange,
  onAnalysisTypeChange,
  onAnalyze,
  loading,
}) => {
  const handleFileUpload = (event) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => onCodeChange(e.target.result?.toString() ?? '')
    reader.readAsText(file)
  }

  return (
    <textarea
      className="code-input-textarea"
      value={code}
      spellCheck={false}
      onChange={(event) => onCodeChange(event.target.value)}
      placeholder="Paste your code here or drop a file..."
    />
  )
}

export default CodeInput
