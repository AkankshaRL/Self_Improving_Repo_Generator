import streamlit as st
import sys
from pathlib import Path
import os
import zipfile
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from graph.build_graph import create_workflow
from schemas.project_spec import AgentState

# Page config
st.set_page_config(
    page_title="AI Code Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
    }
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'generated' not in st.session_state:
    st.session_state.generated = False
if 'zip_path' not in st.session_state:
    st.session_state.zip_path = None
if 'project_name' not in st.session_state:
    st.session_state.project_name = None
if 'history' not in st.session_state:
    st.session_state.history = []
if 'query_input' not in st.session_state:
    st.session_state.query_input = ""
if 'pending_example' not in st.session_state:
    st.session_state.pending_example = None

# Handle pending example - BEFORE any widgets are created
if st.session_state.pending_example:
    st.session_state.query_input = st.session_state.pending_example
    st.session_state.pending_example = None

# Header
st.markdown('<h1 class="main-header">🤖 AI Code Generator</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Generate complete, runnable projects from natural language</p>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Model selection
    model_option = st.selectbox(
        "Model",
        ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
        help="Choose the Gemini model to use"
    )
    
    # Max iterations
    max_iterations = st.slider(
        "Max Repair Iterations",
        min_value=1,
        max_value=5,
        value=3,
        help="Maximum number of repair attempts"
    )
    
    st.divider()
    
    # Statistics
    st.header("📊 Statistics")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Generated", len(st.session_state.history))
    with col2:
        success_count = sum(1 for h in st.session_state.history if h.get('success'))
        st.metric("Success Rate", f"{(success_count/len(st.session_state.history)*100) if st.session_state.history else 0:.0f}%")
    
    st.divider()
    
    # History
    st.header("📜 Recent Projects")
    if st.session_state.history:
        for i, item in enumerate(reversed(st.session_state.history[-5:])):
            status = "✅" if item.get('success') else "❌"
            st.text(f"{status} {item['query'][:30]}...")
    else:
        st.info("No projects generated yet")
    
    st.divider()
    
    # About
    with st.expander("ℹ️ About"):
        st.markdown("""
        **AI Code Generator v3.0**
        
        Multi-agent system that generates complete, 
        runnable code repositories from natural language.
        
        Features:
        - Automated planning & generation
        - Code modernization
        - Runtime verification
        - Error repair loops
        - Production-ready output
        """)

# Main content
tab1, tab2, tab3 = st.tabs(["🚀 Generate", "📦 Examples", "📖 Guide"])

with tab1:
    # Input section
    st.header("What do you want to build?")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_query = st.text_area(
            "Describe your project",
            placeholder="Example: Create a FastAPI todo app with SQLite database and CRUD operations",
            height=100,
            help="Be specific about what you want to build",
            key="query_input"
        )
    
    with col2:
        st.markdown("### Quick Tips")
        st.markdown("""
        ✅ Be specific
        
        ✅ Mention tech stack
        
        ✅ List key features
        
        ✅ Keep it focused
        """)
    
    # Generate button
    generate_col1, generate_col2, generate_col3 = st.columns([1, 2, 1])
    with generate_col2:
        generate_button = st.button("🚀 Generate Project", type="primary", use_container_width=True)
    
    # Generation process
    if generate_button:
        if not user_query or not user_query.strip():
            st.error("⚠️ Please enter a project description")
        else:
            # Check API key
            if not os.getenv("GOOGLE_API_KEY"):
                st.error("❌ GOOGLE_API_KEY not found in environment variables. Please set it in .env file")
            else:
                try:
                    # Progress tracking
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Step 1: Initialize
                    status_text.text("⚙️ Initializing workflow...")
                    progress_bar.progress(10)
                    
                    workflow = create_workflow()
                    
                    # Step 2: Create state
                    status_text.text("📋 Creating project plan...")
                    progress_bar.progress(20)
                    
                    initial_state = AgentState(
                        user_query=user_query,
                        max_iterations=max_iterations
                    )
                    
                    # Step 3: Run workflow
                    status_text.text("🔄 Running multi-agent workflow...")
                    progress_bar.progress(30)
                    
                    # Create container for live updates
                    log_container = st.container()
                    
                    with st.spinner("Generating your project... This may take 1-2 minutes"):
                        final_state = workflow.invoke(initial_state)
                    
                    progress_bar.progress(90)
                    
                    # Get result
                    zip_path = final_state.get('final_zip_path')
                    
                    if zip_path and os.path.exists(zip_path):
                        progress_bar.progress(100)
                        status_text.text("✅ Generation complete!")
                        
                        # Store in session state
                        st.session_state.generated = True
                        st.session_state.zip_path = zip_path
                        st.session_state.project_name = Path(zip_path).stem
                        
                        # Add to history
                        st.session_state.history.append({
                            'query': user_query,
                            'success': True,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'zip_path': zip_path
                        })
                        
                        # Success message
                        st.success("🎉 Project generated successfully!")
                        
                        # Display results
                        st.markdown("---")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.metric("Files Generated", len(final_state.get('generated_files', {})))
                        
                        with col2:
                            st.metric("Repair Iterations", final_state.get('iteration_count', 0))
                        
                        with col3:
                            file_size = os.path.getsize(zip_path) / 1024
                            st.metric("Package Size", f"{file_size:.1f} KB")
                        
                    else:
                        progress_bar.progress(0)
                        st.error("❌ Generation completed but no output file was created")
                        
                        # Add to history as failed
                        st.session_state.history.append({
                            'query': user_query,
                            'success': False,
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        })
                        
                        if final_state.get('errors'):
                            with st.expander("🔍 View Errors"):
                                for error in final_state['errors']:
                                    st.code(error)
                
                except Exception as e:
                    st.error(f"❌ An error occurred during generation")
                    with st.expander("🔍 Error Details"):
                        st.code(str(e))
                        import traceback
                        st.code(traceback.format_exc())
                    
                    # Add to history as failed
                    st.session_state.history.append({
                        'query': user_query,
                        'success': False,
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
    
    # Download section
    if st.session_state.generated and st.session_state.zip_path:
        st.markdown("---")
        st.header("📥 Download Your Project")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"**Project:** `{st.session_state.project_name}`")
            
            # Read zip file
            with open(st.session_state.zip_path, 'rb') as f:
                zip_data = f.read()
            
            # Download button
            st.download_button(
                label="⬇️ Download ZIP File",
                data=zip_data,
                file_name=f"{st.session_state.project_name}.zip",
                mime="application/zip",
                use_container_width=True
            )
        
        with col2:
            # Preview button
            if st.button("👁️ Preview Files", use_container_width=True):
                try:
                    with zipfile.ZipFile(st.session_state.zip_path, 'r') as zip_ref:
                        files = zip_ref.namelist()
                        st.info(f"📁 **{len(files)} files in project:**")
                        for file in files:
                            st.text(f"  📄 {file}")
                except Exception as e:
                    st.error(f"Could not read ZIP: {e}")
        
        # Next steps
        st.markdown("---")
        with st.expander("📖 Next Steps"):
            st.markdown(f"""
            ### How to use your generated project:
            
            1. **Extract the ZIP file:**
               ```bash
               unzip {st.session_state.project_name}.zip
               cd {st.session_state.project_name}
               ```
            
            2. **Create virtual environment:**
               ```bash
               python -m venv venv
               source venv/bin/activate  # Windows: venv\\Scripts\\activate
               ```
            
            3. **Install dependencies:**
               ```bash
               pip install -r requirements.txt
               ```
            
            4. **Configure environment (if needed):**
               ```bash
               cp .env.example .env
               # Edit .env with your settings
               ```
            
            5. **Run the project:**
               ```bash
               python main.py
               ```
            """)

with tab2:
    st.header("📦 Example Prompts")
    st.markdown("Click any example to use it:")
    
    examples = [
        {
            "title": "🌐 FastAPI Todo App",
            "query": "Create a FastAPI todo application with SQLite database, CRUD operations, and Pydantic models",
            "category": "Web API"
        },
        {
            "title": "🤖 LangChain Chatbot",
            "query": "Build a chatbot using LangChain with conversation memory and streaming responses",
            "category": "AI/ML"
        },
        {
            "title": "🕷️ Web Scraper",
            "query": "Create a web scraper using BeautifulSoup that extracts product data and saves to CSV",
            "category": "Data"
        },
        {
            "title": "📊 Data Analyzer",
            "query": "Build a data analysis tool with pandas and matplotlib that reads CSV and generates visualizations",
            "category": "Data"
        },
        {
            "title": "🔐 Authentication System",
            "query": "Create a FastAPI authentication system with JWT tokens, user registration, and login",
            "category": "Web API"
        },
        {
            "title": "📝 Blog API",
            "query": "Build a RESTful blog API with FastAPI, SQLAlchemy ORM, and PostgreSQL support",
            "category": "Web API"
        },
        {
            "title": "🎮 CLI Game",
            "query": "Create a simple command-line number guessing game with score tracking",
            "category": "CLI"
        },
        {
            "title": "📧 Email Sender",
            "query": "Build an email automation script with template support and attachment handling",
            "category": "Automation"
        }
    ]
    
    # Group by category
    categories = {}
    for ex in examples:
        cat = ex['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(ex)
    
    # Display by category
    for category, items in categories.items():
        st.subheader(f"{category}")
        cols = st.columns(2)
        for i, example in enumerate(items):
            with cols[i % 2]:
                # Store in pending_example and rerun
                if st.button(f"{example['title']}", key=f"ex_{category}_{i}", use_container_width=True):
                    st.session_state.pending_example = example['query']
                    st.rerun()
                st.caption(example['query'][:80] + "...")

with tab3:
    st.header("📖 User Guide")
    
    with st.expander("🎯 How It Works", expanded=True):
        st.markdown("""
        ### Multi-Agent Workflow
        
        Your request goes through 6 intelligent agents:
        
        1. **Planner Agent** 📋
           - Analyzes your request
           - Creates project structure
           - Plans all necessary files
        
        2. **Generator Agent** 🔨
           - Writes all code files
           - Creates configs and documentation
           - Generates requirements.txt
        
        3. **Modernizer Agent** 🔄
           - Updates deprecated patterns
           - Uses latest API syntax
           - Applies best practices
        
        4. **Verifier Agent** ✅
           - Checks syntax errors
           - Validates imports
           - Detects runtime issues
        
        5. **Repair Agent** 🔧
           - Fixes detected errors
           - Adds error handling
           - Improves code quality
        
        6. **Integrator Agent** 📦
           - Packages everything
           - Creates ZIP file
           - Ensures completeness
        """)
    
    with st.expander("✍️ Writing Good Prompts"):
        st.markdown("""
        ### Tips for Best Results
        
        **✅ DO:**
        - Be specific about what you want
        - Mention the tech stack (FastAPI, SQLite, etc.)
        - List key features you need
        - Specify file types or structure if important
        
        **❌ DON'T:**
        - Be too vague ("make me a website")
        - Request multiple unrelated apps in one prompt
        - Ask for extremely complex enterprise systems
        - Forget to mention important requirements
        
        ### Examples:
        
        **Good:**
        > "Create a FastAPI todo app with SQLite database, CRUD endpoints, 
        > Pydantic models for validation, and proper error handling"
        
        **Too vague:**
        > "Make me a todo app"
        
        **Too complex:**
        > "Create a full e-commerce platform with user authentication, payment 
        > processing, inventory management, admin dashboard, and mobile app"
        """)
    
    with st.expander("🐛 Troubleshooting"):
        st.markdown("""
        ### Common Issues
        
        **Generation fails or times out:**
        - Try a simpler prompt first
        - Increase max iterations in settings
        - Check your internet connection
        - Verify GOOGLE_API_KEY is set
        
        **Generated code has errors:**
        - The system tries to auto-fix (up to 3 iterations)
        - Check the error details in the expander
        - Try regenerating with clearer requirements
        
        **Download button doesn't appear:**
        - Make sure generation completed successfully
        - Look for error messages above
        - Try refreshing the page
        
        **ZIP file is empty or corrupted:**
        - Check the error logs
        - Try a different browser
        - Ensure enough disk space
        """)
    
    with st.expander("⚙️ Configuration"):
        st.markdown("""
        ### Settings Explained
        
        **Model Selection:**
        - `gemini-2.5-flash-lite`: Fastest, good quality (recommended)
        - `gemini-2.5-flash`: Highest quality, slower
        
        **Max Repair Iterations:**
        - How many times the system tries to fix errors
        - Default: 3 (usually sufficient)
        - Increase for complex projects
        - Decrease for faster (but less reliable) results
        
        ### Environment Setup
        
        Make sure you have:
        1. `.env` file with `GOOGLE_API_KEY`
        2. All dependencies installed (`pip install -r requirements.txt`)
        3. Internet connection for Gemini API
        """)

# Footer
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("🤖 **AI Code Generator v3.0**")
with col2:
    st.markdown("⚡ Powered by Gemini & LangGraph")
with col3:
    st.markdown("📖 [Documentation](#) | 🐛 [Report Issue](#)")