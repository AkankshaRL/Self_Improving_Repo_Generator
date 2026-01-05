import os
from dotenv import load_dotenv
from graph.build_graph import create_workflow
from schemas.project_spec import AgentState
import argparse

def main():
    # Load environment variables
    load_dotenv()
    
    # Verify API key
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY not found in environment variables")
        print("Please create a .env file with your Google API key")
        return
    
    # Parse arguments
    parser = argparse.ArgumentParser(description="Text-to-Code Generator")
    parser.add_argument("query", nargs="*", help="Description of the code to generate")
    parser.add_argument("--output", "-o", default="./output", help="Output directory")
    args = parser.parse_args()
    
    # Get query
    if args.query:
        query = " ".join(args.query)
    else:
        print("\n🤖 Text-to-Code Generator")
        print("=" * 50)
        query = input("\nDescribe what you want to build:\n> ")
    
    if not query.strip():
        print("Error: Query cannot be empty")
        return
    
    print(f"\n📝 Processing: {query}")
    print("=" * 50)
    
    try:
        # Create workflow
        print("\n⚙️  Initializing workflow...")
        workflow = create_workflow()
        
        # Run workflow
        print("🔄 Planning project...")
        initial_state = AgentState(user_query=query)
        
        # LangGraph returns a dictionary, not AgentState object
        final_state_dict = workflow.invoke(initial_state)
        
        # Access the final state from the dictionary
        # The state is stored under a key (usually the node name or a default key)
        # We need to get the actual state data
        if isinstance(final_state_dict, dict):
            # Try different possible keys
            if 'final_zip_path' in final_state_dict:
                final_state = final_state_dict
            else:
                # The state might be nested - get the last value
                final_state = final_state_dict
        else:
            final_state = final_state_dict
        
        # Check result
        zip_path = final_state.get('final_zip_path')
        if zip_path:
            print(f"\n✅ Success! Project generated:")
            print(f"📦 {zip_path}")
            print(f"\n📊 Summary:")
            print(f"   - Files: {len(final_state.get('generated_files', {}))}")
            print(f"   - Iterations: {final_state.get('iteration_count', 0)}")
            errors = final_state.get('errors', [])
            if errors:
                print(f"   - Final errors: {len(errors)}")
        else:
            print("\n❌ Failed to generate project")
            errors = final_state.get('errors', [])
            if errors:
                print("\nErrors:")
                for error in errors:
                    print(f"  - {error}")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()