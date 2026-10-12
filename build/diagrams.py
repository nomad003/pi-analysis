# Shared Mermaid sources. Layer classes (:::ai etc.) and `box <layer>` are themed at render time by assets/mmd.js.
# Convention: structure diagrams flow top->bottom (TB); linear pipelines flow left->right (LR).
# Solid edge = call / dependency; dashed edge = event, async or devDependency.
D = {}

D["packages"] = """flowchart TB
  EV["pi-evals"]:::infra
  subgraph STACK["Agent stack · pulled in by pi-coding-agent"]
    CA["pi-coding-agent"]:::coding
    AG["pi-agent-core"]:::agent
    TUI["pi-tui"]:::tui
    MCP["pi-mcp"]:::infra
    CM["pi-codemode"]:::infra
    AI["pi-ai"]:::ai
    TEL["pi-telemetry"]:::infra
  end
  subgraph REMOTE["Durable & remote sessions"]
    SRV["pi-server"]:::infra
    CLI["pi-client"]:::infra
    ENV["pi-env"]:::infra
    PROT["pi-protocol"]:::infra
    DUR["pi-durable"]:::infra
  end
  CH["chord · composition runtime"]:::infra
  CA --> AG
  CA --> TUI
  CA --> MCP
  CA --> CM
  CA --> AI
  AG --> AI
  AI --> TEL
  SRV --> PROT
  CLI --> PROT
  ENV --> DUR
  DUR --> AI
  CA --> CH
  SRV --> CH
  CLI --> CH
  ENV --> CH
  PROT --> CH
  DUR --> CH
  EV -.->|dev| CA
  EV -.->|dev| AI
  CA -.->|dev| SRV
  CA -.->|dev| CLI
  CA -.->|dev| PROT"""

D["layers"] = """%%{init: {"flowchart": {"nodeSpacing": 26, "rankSpacing": 46}}}%%
flowchart TB
  IM["InteractiveMode"]:::modes
  PM["runPrintMode()<br/>text · json"]:::modes
  RM["runRpcMode()<br/>JSONL stdin / stdout"]:::modes
  TUI["pi-tui<br/>differential renderer"]:::tui
  RT["AgentSessionRuntime"]:::coding
  AS["AgentSession"]:::coding
  SM["SessionManager"]:::coding
  ER["ExtensionRunner"]:::ext
  TL["tools<br/>read bash edit write<br/>grep find ls powershell"]:::coding
  CP["compaction"]:::coding
  A["pi-agent-core · Agent"]:::agent
  L["runLoop()"]:::agent
  MD["pi-ai · Models<br/>42 providers"]:::ai
  API["api/* · 10 chat APIs"]:::ai
  ES["AssistantMessageEventStream"]:::ai
  IM --> TUI
  IM --> RT
  PM --> RT
  RM --> RT
  RT --> AS
  AS --> SM
  AS --> ER
  AS --> A
  AS --> TL
  AS --> CP
  A --> L
  L -->|"streamFn · ModelRuntime"| MD
  MD --> API --> ES
  ES -.->|events| L
"""

D["loop"] = """%%{init: {"flowchart": {"rankSpacing": 26, "nodeSpacing": 30, "padding": 10}}}%%
flowchart TB
  S(["runLoop() · poll getSteeringMessages()"]):::term
  IN{"tool calls or<br/>steering pending?"}:::dec
  TURN["prepareNextTurn() · inject pending<br/>prepareRequest()"]:::coding
  STR["streamAssistantResponse()<br/>transformContext → convertToLlm → streamFn"]:::agent
  ER{"error /<br/>aborted?"}:::dec
  TC{"tool calls?"}:::dec
  FAIL["fail every call<br/>args may be truncated"]:::err
  EX["executeToolCalls()<br/>sequential · parallel"]:::agent
  FT["finishTurn() → decision<br/>turn_end"]:::coding
  D{"decision<br/>= end?"}:::dec
  FU{"getFollowUpMessages()<br/>non-empty?"}:::dec
  CONT{"decision<br/>= continue?"}:::dec
  END(["agent_end"]):::term
  S --> IN
  IN -->|yes| TURN --> STR --> ER
  ER -->|no| TC
  TC -->|yes| EX --> FT
  TC -->|"stop = length"| FAIL --> FT
  TC -->|no| FT
  FT --> D
  D -->|"no · poll steering"| IN
  IN -->|no| FU
  FU -->|"yes · outer loop"| IN
  FU -->|no| CONT
  CONT -->|"yes"| IN
  CONT -->|no| END
  ER -->|yes| END
  D -->|yes| END"""

D["toolexec"] = """%%{init: {"flowchart": {"rankSpacing": 26, "nodeSpacing": 30, "padding": 10}}}%%
flowchart TB
  TC(["toolCall from assistant message"]):::term
  F{"tool found?"}:::dec
  PA["tool.prepareArguments()"]:::agent
  V{"validateToolArguments()<br/>TypeBox schema"}:::dec
  B{"beforeToolCall()<br/>ext · tool_call"}:::ext
  X["tool.execute(id, args, signal, onUpdate)<br/>onUpdate → tool_execution_update"]:::agent
  A["afterToolCall()<br/>ext · tool_result"]:::ext
  ERR["createErrorToolResult()<br/>isError: true"]:::err
  END["tool_execution_end"]:::agent
  R(["ToolResultMessage"]):::term
  TC --> F
  F -->|yes| PA --> V
  V -->|ok| B
  B -->|allow| X --> A --> END
  F -->|no| ERR
  V -->|invalid| ERR
  B -->|block| ERR
  X -.->|throws| ERR
  ERR --> END --> R"""

D["sequence"] = """sequenceDiagram
  autonumber
  box modes Run mode
    participant IM as InteractiveMode
  end
  box coding pi-coding-agent
    participant AS as AgentSession
    participant EX as ExtensionRunner
    participant SM as SessionManager
    participant T as Tool
  end
  box agent pi-agent-core
    participant A as Agent
    participant L as runLoop
  end
  box ai pi-ai
    participant P as streamFn
  end
  IM->>AS: prompt(text)
  AS->>EX: input · expand skills
  AS->>EX: before_agent_start
  AS->>A: agent.prompt()
  A->>L: runAgentLoop()
  L-->>AS: message_end(user)
  AS->>SM: appendMessage()
  L->>EX: context
  L->>P: streamFn(model, context)
  P-->>L: text_delta · toolcall_*
  L-->>AS: message_update
  AS-->>IM: re-render
  L-->>AS: message_end(assistant)
  AS->>SM: appendMessage()
  L->>EX: tool_call
  L->>T: execute(args, onUpdate)
  T-->>L: updates · result
  L->>EX: tool_result
  L-->>AS: message_end(toolResult)
  AS->>SM: appendMessage()
  L->>P: next request
  P-->>L: done(stop)
  L-->>AS: turn_end · agent_end
  AS-->>IM: idle"""

D["sequence_compact"] = """sequenceDiagram
  box modes Run mode
    participant IM as InteractiveMode
  end
  box coding pi-coding-agent
    participant AS as AgentSession
    participant EX as ExtensionRunner
    participant T as Tool
  end
  box agent pi-agent-core
    participant L as runLoop
  end
  box ai pi-ai
    participant P as streamFn
  end
  IM->>AS: prompt(text)
  AS->>EX: input · before_agent_start
  AS->>L: agent.prompt() → runAgentLoop()
  L->>EX: context
  L->>P: streamFn(model, context)
  P-->>L: text_delta … done(toolUse)
  L-->>IM: message_update → re-render
  L->>EX: tool_call
  L->>T: execute(args, onUpdate)
  T-->>L: result
  L->>EX: tool_result
  L->>P: next request
  P-->>L: done(stop)
  L-->>AS: turn_end · agent_end"""

D["classes"] = """classDiagram
  direction TB
  class AgentSessionRuntime {
    +session AgentSession
    +services AgentSessionServices
    +newSession()
    +switchSession()
    +fork()
    +importFromJsonl()
    +dispose()
  }
  class AgentSession {
    +agent Agent
    +sessionManager SessionManager
    +prompt(text, options)
    +steer() / followUp()
    +setModel() / cycleModel()
    +setThinkingLevel()
    +compact() / navigateTree()
    +bindExtensions() / reload()
    +executeBash()
  }
  class Agent {
    +state AgentState
    +streamFunction StreamFn
    +toolExecution ToolExecutionMode
    +convertToLlm / transformContext
    +beforeToolCall / afterToolCall
    +prepareRequest / prepareNextTurn
    +finishTurn
    +subscribe(listener)
    +prompt(input, images)
    +continue()
    +steer() / followUp()
    +abort() / waitForIdle() / reset()
  }
  class AgentTool {
    <<interface>>
    +name / label / parameters
    +prepareArguments(args)
    +executionMode
    +execute(id, args, signal, onUpdate)
  }
  class SessionManager {
    -byId / leafId
    +newSession()
    +appendMessage() / appendCompaction()
    +getBranch() / getTree()
    +branch() / branchWithSummary()
    +buildSessionContext()
    +createBranchedSession()
  }
  class ExtensionRunner {
    +bindCore(actions)
    +setUIContext(ui, mode)
    +emit(event)
    +emitInput() / emitContext()
    +emitToolCall() / emitToolResult()
    +emitBeforeAgentStart()
    +emitBeforeProviderRequest()
  }
  class ModelRuntime {
    +streamSimple(model, context)
    +checkAuth(provider)
    +registerProvider(name, config)
  }
  class Models {
    <<interface>>
    +getProviders() / getModel()
    +refresh() / checkAuth()
    +getAvailable()
    +streamSimple()
  }
  class Provider {
    <<interface>>
    +id / name / auth
    +getModels()
    +streamSimple()
  }
  AgentSessionRuntime --> AgentSession : session
  AgentSession --> Agent : agent
  AgentSession --> SessionManager : sessionManager
  AgentSession --> ExtensionRunner
  AgentSession --> ModelRuntime
  Agent o-- AgentTool : state.tools
  ModelRuntime ..|> Models
  Models o-- Provider
  cssClass "AgentSessionRuntime,AgentSession,SessionManager,ModelRuntime" coding
  cssClass "ExtensionRunner" ext
  cssClass "Agent,AgentTool" agent
  cssClass "Models,Provider" ai"""

D["session"] = """%%{init: {"flowchart": {"rankSpacing": 26, "nodeSpacing": 30, "padding": 10}}}%%
flowchart TB
  H["session header<br/>version 3 · id · cwd"]:::infra
  U1["message · user<br/>fix the failing test"]
  A1["message · assistant<br/>+ toolCall(bash)"]
  T1["message · toolResult"]
  A2["message · assistant<br/>done"]
  U2["message · user<br/>also add tests"]
  C1["compaction<br/>summary · firstKeptEntryId"]:::coding
  U4["message · user<br/>continue"]
  BS["branch_summary<br/>fromId → abandoned leaf"]:::coding
  U3["message · user<br/>try a different approach"]
  LEAF(["leafId"]):::term
  H --> U1 --> A1 --> T1 --> A2
  A2 --> U2 --> C1 --> U4
  A2 --> BS --> U3
  LEAF -.-> U3"""

D["compaction"] = """%%{init: {"flowchart": {"rankSpacing": 26, "nodeSpacing": 30, "padding": 10}}}%%
flowchart TB
  MAN(["manual · /compact"]):::term
  THR(["threshold<br/>tokens > window − reserveTokens"]):::term
  OVF(["overflow<br/>context overflow · length stop"]):::err
  PC["prepareCompaction() · findCutPoint()<br/>emit compaction_start(reason)"]:::coding
  HOOK{"ext ·<br/>session_before_compact"}:::ext
  CAN(["cancelled"]):::term
  CUS["extension's<br/>compaction"]:::ext
  GS["compact() → generateSummary()<br/>LLM summarizes older entries"]:::coding
  AP["appendCompaction()<br/>session_compact · compaction_end"]:::coding
  R{"overflow<br/>willRetry?"}:::dec
  RETRY["agent.continue()<br/>retry once"]:::agent
  DONE(["continue"]):::term
  MAN --> PC
  THR --> PC
  OVF --> PC
  PC --> HOOK
  HOOK -->|cancel| CAN
  HOOK -->|compaction| CUS
  HOOK -->|none| GS
  CUS --> AP
  GS --> AP
  AP --> R
  R -->|yes| RETRY
  R -->|no| DONE"""

D["extensions"] = """sequenceDiagram
  box coding pi-coding-agent
    participant M as main.ts
    participant RL as ResourceLoader
    participant S as AgentSession
  end
  box ext Extensions
    participant R as ExtensionRunner
    participant X as extension
  end
  box modes Run mode
    participant MO as mode
  end
  M->>RL: reload()
  RL->>RL: packageManager.resolve()
  RL->>X: jiti.import() · factory(pi)
  X-->>RL: registerTool · on(…)
  M->>S: createAgentSessionFromServices()
  S->>R: bindCore(actions)
  M->>MO: start mode
  MO->>S: bindExtensions()
  S->>R: setUIContext()
  R-->>X: session_start
  loop every prompt
    R-->>X: input · before_agent_start
    R-->>X: context
    R-->>X: before_provider_request
    R-->>X: tool_call · tool_result
    R-->>X: turn_end · agent_end
  end
  R-->>X: session_compact · session_tree
  R-->>X: session_shutdown"""

D["modes"] = """flowchart LR
  CLI(["pi argv"]):::term
  R{"resolveAppMode()"}:::dec
  RPC["runRpcMode()<br/>33 JSONL commands in · events out"]:::modes
  JS["runPrintMode() · json<br/>events as JSON lines"]:::modes
  PR["runPrintMode() · text<br/>one-shot, final text"]:::modes
  IM["InteractiveMode<br/>editor · chat viewport · /commands"]:::modes
  RT["AgentSessionRuntime<br/>→ AgentSession"]:::coding
  TUI["pi-tui"]:::tui
  CLI --> R
  R -->|"--mode rpc"| RPC
  R -->|"--mode json"| JS
  R -->|"-p · non-TTY"| PR
  R -->|TTY| IM
  RPC --> RT
  JS --> RT
  PR --> RT
  IM --> RT
  IM --> TUI"""

D["providers"] = """%%{init: {"flowchart": {"nodeSpacing": 18, "rankSpacing": 70}}}%%
flowchart LR
  M["ModelRuntime → Models<br/>getModel · checkAuth"]:::coding
  subgraph PV["providers/*.ts · 42 built-in"]
    an["anthropic"]:::ai
    orr["openrouter"]:::ai
    gc["github-copilot"]:::ai
    oc["groq · deepseek · …"]:::ai
    oa["openai · xai"]:::ai
    cx["openai-codex"]:::ai
    az["azure"]:::ai
    ms["mistral"]:::ai
    gg["google"]:::ai
    gv["google-vertex"]:::ai
    br["amazon-bedrock"]:::ai
    rd["radius"]:::ai
  end
  subgraph AP["api/*.ts · 10 KnownApi · lazy"]
    AM["anthropic-messages"]:::ai
    OC["openai-completions"]:::ai
    OR["openai-responses"]:::ai
    OCR["openai-codex-responses"]:::ai
    AZ["azure-openai-responses"]:::ai
    MC["mistral-conversations"]:::ai
    GA["google-generative-ai"]:::ai
    GV["google-vertex"]:::ai
    BC["bedrock-converse-stream"]:::ai
    PIM["pi-messages"]:::ai
  end
  EV["AssistantMessageEventStream<br/>start · text_* · thinking_*<br/>toolcall_* · done · error"]:::ai
  M --> PV
  an --> AM
  orr --> AM
  orr --> OC
  gc --> AM
  gc --> OC
  gc --> OR
  oc --> OC
  oa --> OR
  cx --> OCR
  az --> AZ
  ms --> MC
  gg --> GA
  gv --> GV
  br --> BC
  rd --> PIM
  AP --> EV
"""

D["tui"] = """flowchart LR
  K(["stdin"]):::term
  SB["ProcessTerminal<br/>StdinBuffer → keys"]:::tui
  F["focused Component<br/>.handleInput()"]:::tui
  EVT["agent events<br/>InteractiveMode"]:::modes
  RQ["requestRender()<br/>nextTick batch · ≥ 16 ms"]:::tui
  DR["doRender()<br/>render(width) → string[]"]:::tui
  OUT(["diff vs previousLines<br/>write changed lines"]):::term
  K --> SB --> F --> RQ
  EVT --> RQ
  RQ --> DR --> OUT"""

# ---- Slide variants: same theme / palette / naming, fewer nodes so text stays legible on a 16:9 slide.
D["loop_compact"] = """flowchart TB
  S(["prompt / continue"]):::term
  IN{"tool calls or<br/>steering pending?"}:::dec
  TURN["prepareNextTurn()<br/>prepareRequest()"]:::coding
  STR["streamAssistantResponse()"]:::agent
  TC{"tool calls?"}:::dec
  EX["executeToolCalls()"]:::agent
  FT["finishTurn() · turn_end"]:::coding
  FU{"follow-ups<br/>queued?"}:::dec
  END(["agent_end"]):::term
  S --> IN
  IN -->|yes| TURN --> STR --> TC
  TC -->|yes| EX --> FT
  TC -->|no| FT
  FT -->|inner loop| IN
  IN -->|no| FU
  FU -->|"yes · outer loop"| IN
  FU -->|no| END"""

D["toolexec_compact"] = """flowchart LR
  TC(["toolCall"]):::term
  PV{"find · prepareArguments<br/>validateToolArguments"}:::dec
  B{"beforeToolCall<br/>ext · tool_call"}:::ext
  X["execute()<br/>tool_execution_update"]:::agent
  A["afterToolCall<br/>ext · tool_result"]:::ext
  R(["ToolResultMessage"]):::term
  ERR["error result<br/>isError: true"]:::err
  TC --> PV
  PV -->|ok| B
  B -->|allow| X --> A --> R
  PV -->|"missing · invalid"| ERR
  B -->|block| ERR
  ERR --> R"""

D["classes_compact"] = """classDiagram
  direction LR
  class AgentSessionRuntime {
    +session
    +fork() / switchSession()
  }
  class AgentSession {
    +prompt()
    +compact()
    +bindExtensions()
  }
  class Agent {
    +state
    +prompt() / continue()
    +steer() / followUp()
  }
  class AgentTool {
    <<interface>>
    +execute()
  }
  class SessionManager {
    +appendMessage()
    +buildSessionContext()
  }
  class ExtensionRunner {
    +emit()
    +bindCore()
  }
  class ModelRuntime {
    +streamSimple()
  }
  class Models {
    <<interface>>
    +getModel()
  }
  AgentSessionRuntime --> AgentSession
  AgentSession --> Agent
  AgentSession --> SessionManager
  AgentSession --> ExtensionRunner
  AgentSession --> ModelRuntime
  Agent o-- AgentTool
  ModelRuntime ..|> Models
  cssClass "AgentSessionRuntime,AgentSession,SessionManager,ModelRuntime" coding
  cssClass "ExtensionRunner" ext
  cssClass "Agent,AgentTool" agent
  cssClass "Models" ai"""

D["providers_compact"] = """flowchart LR
  subgraph PV["providers · selection of 42"]
    an["anthropic"]:::ai
    oa["openai · xai"]:::ai
    oc["groq · deepseek · openrouter"]:::ai
    gg["google · google-vertex"]:::ai
    br["amazon-bedrock"]:::ai
  end
  subgraph AP["chat APIs · selection of 10"]
    AM["anthropic-messages"]:::ai
    OR["openai-responses"]:::ai
    OC["openai-completions"]:::ai
    GA["google-generative-ai<br/>google-vertex"]:::ai
    BC["bedrock-converse-stream"]:::ai
  end
  EV["AssistantMessageEventStream"]:::ai
  L["runLoop()"]:::agent
  an --> AM
  oa --> OR
  oc --> OC
  gg --> GA
  br --> BC
  AP --> EV --> L"""

D["extensions_compact"] = """sequenceDiagram
  box coding pi-coding-agent
    participant RL as ResourceLoader
    participant S as AgentSession
  end
  box ext Extensions
    participant R as ExtensionRunner
    participant X as extension
  end
  RL->>X: jiti.import() · factory(pi)
  X-->>RL: registerTool · on(…)
  S->>R: bindCore() · setUIContext()
  R-->>X: session_start
  loop every prompt
    R-->>X: input · context
    R-->>X: tool_call · tool_result
    R-->>X: turn_end · agent_end
  end
  R-->>X: session_shutdown"""

D["sequence_compact"] = """sequenceDiagram
  box modes Run mode
    participant IM as InteractiveMode
  end
  box coding pi-coding-agent
    participant AS as AgentSession
    participant T as Tool
  end
  box agent pi-agent-core
    participant L as runLoop
  end
  box ai pi-ai
    participant P as streamFn
  end
  IM->>AS: prompt(text)
  AS->>L: agent.prompt()
  L->>P: request 1
  P-->>L: text_delta · done(toolUse)
  L-->>IM: message_update
  L->>T: execute(args)
  T-->>L: result
  L->>P: request 2
  P-->>L: done(stop)
  L-->>AS: agent_end"""
