import streamlit as st
import requests
import io

# The URL where your FastAPI server is running
API_URL = "http://127.0.0.1:8000"

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Mini Social", page_icon="📱", layout="centered")

# Hide Streamlit's default menu and footer for a cleaner app look
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stImage > img {border-radius: 10px;} /* Round the corners of images */
    </style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
# This keeps track of whether the user is logged in
if "token" not in st.session_state:
    st.session_state["token"] = None
if "current_page" not in st.session_state:
    st.session_state["current_page"] = "Feed"

# --- HELPER FUNCTIONS ---
def logout():
    st.session_state["token"] = None
    st.session_state["current_page"] = "Feed"
    st.rerun()

# --- AUTHENTICATION UI (Login / Register) ---
def render_auth():
    st.title("📱 Mini Social")
    st.write("Welcome! Please log in or register to continue.")
    
    tab1, tab2 = st.tabs(["Log In", "Register"])
    
    with tab1:
        st.subheader("Log In")
        login_email = st.text_input("Email", key="login_email")
        login_password = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("Log In", type="primary"):
            # FastAPI expects OAuth2 form data for login
            res = requests.post(f"{API_URL}/login", data={"username": login_email, "password": login_password})
            if res.status_code == 200:
                st.session_state["token"] = res.json()["access_token"]
                st.success("Logged in successfully!")
                st.rerun()
            else:
                st.error(res.json().get("detail", "Login failed"))

    with tab2:
        st.subheader("Register")
        reg_email = st.text_input("Email", key="reg_email")
        reg_password = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("Register"):
            # FastAPI expects JSON for registration
            res = requests.post(f"{API_URL}/register", json={"email": reg_email, "password": reg_password})
            if res.status_code == 201:
                st.success("Registered successfully! You can now log in.")
            else:
                st.error(res.json().get("detail", "Registration failed"))

# --- MAIN APP UI ---
def render_app():
    # Sidebar Navigation
    with st.sidebar:
        st.title("📱 Mini Social")
        st.write("Navigation")
        if st.button("🏠 Home (Feed)", use_container_width=True):
            st.session_state["current_page"] = "Feed"
            st.rerun()
        if st.button("➕ Create Post", use_container_width=True):
            st.session_state["current_page"] = "Create Post"
            st.rerun()
        
        st.divider()
        if st.button("🚪 Log Out", use_container_width=True):
            logout()

    # View: Feed
    if st.session_state["current_page"] == "Feed":
        st.header("Home Feed")
        
        # Fetch posts from FastAPI
        res = requests.get(f"{API_URL}/posts/")
        if res.status_code == 200:
            posts = res.json()
            if not posts:
                st.info("No posts yet. Be the first to post something!")
            
            # Instagram-style feed: Centered column
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                # Reverse the list so newest posts are at the top
                for post in reversed(posts):
                    with st.container(border=True):
                        # Username/Owner ID
                        st.markdown(f"**👤 User #{post['owner_id']}**")
                        
                        # Image (if it exists)
                        if post.get("image_url"):
                            st.image(post["image_url"], use_container_width=True)
                        
                        # Caption
                        st.write(post["content"])
                        st.caption("❤️ Like 💬 Comment") # Placeholders for future features
                        st.write("") # Spacing
        else:
            st.error("Could not fetch posts. Is the backend running?")

    # View: Create Post
    elif st.session_state["current_page"] == "Create Post":
        st.header("Create a New Post")
        
        with st.form("new_post_form", clear_on_submit=True):
            content = st.text_area("What's on your mind?", max_chars=500)
            uploaded_file = st.file_uploader("Choose an image (optional)", type=["jpg", "jpeg", "png"])
            
            submit = st.form_submit_button("Share Post", type="primary")
            
            if submit:
                if not content:
                    st.warning("Please write a caption!")
                else:
                    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
                    
                    # Setup multipart form data
                    data = {"content": content}
                    files = {}
                    if uploaded_file is not None:
                        files = {"image": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    
                    with st.spinner("Uploading to ImageKit and saving..."):
                        res = requests.post(f"{API_URL}/posts/", headers=headers, data=data, files=files)
                        
                    if res.status_code == 201:
                        st.success("Post created successfully!")
                        st.session_state["current_page"] = "Feed"
                        st.rerun()
                    else:
                        st.error("Failed to create post.")

# --- ROUTER ---
# If no token, show login. If token exists, show the main app.
if st.session_state["token"] is None:
    render_auth()
else:
    render_app()