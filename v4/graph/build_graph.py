from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from schemas.project_spec import AgentState
from agents.planner import PlannerAgent
from agents.generator import GeneratorAgent
from agents.verifier import VerifierAgent
from agents.modernizer import ModernizerAgent
from agents.integrator import IntegratorAgent
from dotenv import load_dotenv

load_dotenv()

def create_workflow():
    '''Optimized workflow: Minimal LLM calls, maximum quality'''
    
    # Single LLM instance
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash-lite",  # Faster, cheaper
        temperature=0.1,  # Consistent output
    )
    
    # Initialize agents
    planner = PlannerAgent(llm)  # 0-1 LLM calls (templates first)
    generator = GeneratorAgent(llm)  # N LLM calls (one per file)
    modernizer = ModernizerAgent()  # 0 LLM calls (rule-based)
    verifier = VerifierAgent()  # 0 LLM calls (static analysis)
    integrator = IntegratorAgent()  # 0 LLM calls (file ops)
    
    workflow = StateGraph(AgentState)
    
    def plan_node(state: AgentState) -> AgentState:
        print("📋 Planning...")
        state.project_spec = planner.plan(state.user_query)
        print(f"   ✅ {len(state.project_spec.files)} files planned")
        return state
    
    def generate_node(state: AgentState) -> AgentState:
        print("🔨 Generating code...")
        state.generated_files = generator.generate_files(
            state.project_spec,
            previous_errors=state.errors if state.iteration_count > 0 else None
        )
        return state
    
    def modernize_node(state: AgentState) -> AgentState:
        print("🔄 Modernizing...")
        state.generated_files = modernizer.modernize_files(state.generated_files)
        return state
    
    def verify_node(state: AgentState) -> AgentState:
        print("✅ Verifying...")
        results, errors = verifier.verify_files(state.generated_files)
        state.verification_results = results
        state.errors = errors
        
        if errors:
            print(f"   ⚠️  {len(errors)} issues found")
        else:
            print("   ✅ All checks passed")
        return state
    
    def integrate_node(state: AgentState) -> AgentState:
        print("📦 Packaging...")
        state.final_zip_path = integrator.package_project(
            state.project_spec,
            state.generated_files
        )
        return state
    
    def should_retry(state: AgentState) -> str:
        '''Retry only for critical errors, max 2 iterations'''
        
        if not state.errors or state.iteration_count >= 2:
            return "integrate"
        
        # Only retry for syntax errors
        critical = [e for e in state.errors if 'Syntax error' in e or 'SyntaxError' in e]
        
        if critical:
            print(f"   🔧 Retry {state.iteration_count + 1}/2")
            state.iteration_count += 1
            return "generate"
        
        return "integrate"
    
    # Build graph
    workflow.add_node("plan", plan_node)
    workflow.add_node("generate", generate_node)
    workflow.add_node("modernize", modernize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("integrate", integrate_node)
    
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "generate")
    workflow.add_edge("generate", "modernize")
    workflow.add_edge("modernize", "verify")
    workflow.add_conditional_edges("verify", should_retry, {
        "generate": "generate",
        "integrate": "integrate"
    })
    workflow.add_edge("integrate", END)
    
    return workflow.compile()