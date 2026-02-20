const QuickActions = ({ onAction, hasResults }) => {
  const actions = [
    {
      id: 'uml',
      label: 'Generate UML',
      icon: '📊',
      description: 'Create UML diagrams from code',
    },
    {
      id: 'diagrams',
      label: 'View Diagrams',
      icon: '🔍',
      description: 'Browse CFG and DFG graphs',
      disabled: !hasResults,
    },
    {
      id: 'export',
      label: 'Export JSON',
      icon: '💾',
      description: 'Download analysis as JSON',
      disabled: !hasResults,
    },
    {
      id: 'report',
      label: 'Generate Report',
      icon: '📄',
      description: 'Create text report',
      disabled: !hasResults,
    },
  ]

  return (
    <div className="quick-actions-panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="panel-icon">✨</span>
          <h2>Quick Actions</h2>
        </div>
      </div>

      <div className="quick-actions-list">
        {actions.map((action) => (
          <button
            key={action.id}
            className={`quick-action-btn ${action.disabled ? 'disabled' : ''}`}
            onClick={() => !action.disabled && onAction(action.id)}
            disabled={action.disabled}
            title={action.disabled ? 'Run analysis first' : action.description}
          >
            <span className="action-icon">{action.icon}</span>
            <span className="action-label">{action.label}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

export default QuickActions

