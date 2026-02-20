import { useState } from 'react'
import plantumlEncoder from 'plantuml-encoder'

export default function UMLDiagramGenerator() {
  const [code, setCode] = useState(`@startuml
class User {
  - id: int
  - name: string
  - email: string
  + login()
  + logout()
}

class Order {
  - orderId: int
  - date: Date
  + create()
  + cancel()
}

User "1" -- "*" Order
@enduml`)

  const [imageUrl, setImageUrl] = useState('')
  const [loading, setLoading] = useState(false)

  const generate = () => {
    setLoading(true)

    const encoded = plantumlEncoder.encode(code)
    const url = `https://www.plantuml.com/plantuml/png/${encoded}`

    const img = new Image()

    img.onload = () => {
      setImageUrl(url)
      setLoading(false)
    }

    img.onerror = () => {
      setLoading(false)
      alert('Invalid PlantUML syntax!')
    }

    img.src = url
  }

  const examples = {
    class: `@startuml
class Car {
  + brand: string
  + model: string
  + drive()
}
class Engine {
  + hp: int
}
Car --> Engine
@enduml`,

    sequence: `@startuml
actor User
participant App
User -> App: Request
App --> User: Response
@enduml`,

    usecase: `@startuml
actor Customer
(Customer) --> (Buy Product)
@enduml`,

    activity: `@startuml
start
:Browse products;
:Select item;
if (In stock?) then (yes)
  :Add to cart;
  :Checkout;
else (no)
  :Show error;
endif
stop
@enduml`,

    state: `@startuml
[*] --> Idle
Idle --> Processing : request
Processing --> Success : done
Processing --> Error : fail
@enduml`,

    component: `@startuml
package "Frontend" {
  [React UI]
}

package "Backend" {
  [API Server]
  [Database]
}

[React UI] --> [API Server]
[API Server] --> [Database]
@enduml`,

    erd: `@startuml
entity User {
  * id : INT
  * name : VARCHAR
}

entity Orders {
  * order_id : INT
  * user_id : INT
  * amount : DOUBLE
}

User ||--o{ Orders : places
@enduml`,
  }

  return (
    <div className="uml-generator-container">
      <div className="uml-generator-card">
        <div className="uml-generator-header">
          <h1>🎨 UML Diagram Generator</h1>
          <p>Generate UML using PlantUML</p>
        </div>

        <div className="uml-generator-grid">
          {/* Left Panel: Editor */}
          <div className="uml-editor-panel">
            <div className="uml-editor-title">PlantUML Code</div>

            {/* Example Buttons */}
            <div className="uml-examples">
              {Object.keys(examples).map((t) => (
                <button
                  key={t}
                  className="uml-example-btn"
                  onClick={() => setCode(examples[t])}
                >
                  {t.toUpperCase()}
                </button>
              ))}
            </div>

            <textarea
              value={code}
              onChange={(e) => setCode(e.target.value)}
              className="uml-code-textarea"
            />

            <div className="uml-editor-actions">
              <button onClick={generate} className="uml-generate-btn">
                Generate Diagram
              </button>

              <button
                onClick={() => {
                  setCode('')
                  setImageUrl('')
                }}
                className="uml-clear-btn"
              >
                Clear
              </button>
            </div>
          </div>

          {/* Right Panel: Preview */}
          <div className="uml-preview-panel">
            <h2>Preview</h2>

            <div className="uml-preview-container">
              {!imageUrl && !loading && (
                <p className="uml-preview-placeholder">Your diagram will appear here</p>
              )}

              {loading && <p className="uml-loading">Generating...</p>}

              {imageUrl && !loading && (
                <img src={imageUrl} alt="uml diagram" className="uml-diagram-image" />
              )}
            </div>

            {imageUrl && (
              <a className="uml-download-btn" href={imageUrl} download="uml-diagram.png">
                Download PNG
              </a>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
