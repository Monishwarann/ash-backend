import os

html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates', 'index.html')
js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'script.js')

with open(html_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

firebase_scripts = """    <!-- Firebase SDK -->
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-app-compat.js"></script>
    <script src="https://www.gstatic.com/firebasejs/9.22.1/firebase-auth-compat.js"></script>
    <!-- Dashboard JavaScript -->"""

html_content = html_content.replace("<!-- Dashboard JavaScript -->", firebase_scripts)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_content)


with open(js_path, 'r', encoding='utf-8') as f:
    js_content = f.read()

firebase_init = """// Firebase Config
const firebaseConfig = {
    apiKey: 'AIzaSyCtbDdM4NMpfe67x3pQEAGIynr-RUTaW7M',
    authDomain: 'medi-c3916.firebaseapp.com',
    projectId: 'medi-c3916',
};
firebase.initializeApp(firebaseConfig);

let authToken = null;

firebase.auth().onAuthStateChanged(async (user) => {
    if (user) {
        authToken = await user.getIdToken();
        currentUserId = user.uid;
        currentUsername = user.email.split('@')[0];
        isAuthed = true;
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> ${currentUsername}`;
        document.getElementById('auth-toggle-btn').innerHTML = `<i class="fa-solid fa-sign-out-alt"></i> Logout`;
        fetchHistory();
    } else {
        authToken = null;
        isAuthed = false;
        currentUserId = 1;
        currentUsername = 'demo';
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> Demo Mode`;
    }
});

"""

# Prepend firebase init to js_content
js_content = firebase_init + js_content

# Remove checkAuthSession logic since we use onAuthStateChanged
js_content = js_content.replace("""// Check Session / Defaults
function checkAuthSession() {
    // Automatically try to login as demo if not logged in
    const cachedUser = localStorage.getItem('user_id');
    if (cachedUser) {
        currentUserId = parseInt(cachedUser);
        currentUsername = localStorage.getItem('username');
        isAuthed = true;
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> ${currentUsername}`;
        document.getElementById('auth-toggle-btn').innerHTML = `<i class="fa-solid fa-sign-out-alt"></i> Logout`;
    } else {
        // Set guest values
        currentUserId = 1;
        currentUsername = 'demo';
        document.getElementById('user-badge').innerHTML = `<i class="fa-solid fa-circle-user"></i> Demo Mode`;
    }
}""", "function checkAuthSession() { /* Handled by Firebase Auth State Observer */ }")

# Update get API headers helper
auth_headers_js = """function getAuthHeaders() {
    return {
        'Content-Type': 'application/json',
        'Authorization': authToken ? `Bearer ${authToken}` : ''
    };
}"""
js_content = js_content.replace("function checkAuthSession() { /* Handled by Firebase Auth State Observer */ }", "function checkAuthSession() { /* Handled by Firebase Auth State Observer */ }\n\n" + auth_headers_js)

# Replace fetch calls to use getAuthHeaders
js_content = js_content.replace("headers: { 'Content-Type': 'application/json' },", "headers: getAuthHeaders(),")

# Also for get requests like fetchHistory:
js_content = js_content.replace("await fetch(`/api/history/${currentUserId}`);", "await fetch(`/api/history/${currentUserId}`, { headers: getAuthHeaders() });")

# For API telemetry latest
js_content = js_content.replace("await fetch(`/api/telemetry/latest/${currentUserId}`);", "await fetch(`/api/telemetry/latest/${currentUserId}`, { headers: getAuthHeaders() });")

# And handleAuth login logic
old_handle_auth = """    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();
        
        if (response.ok) {
            showToast(data.message);
            closeAuthModal();
            
            if (authTab === 'login') {
                localStorage.setItem('user_id', data.user_id);
                localStorage.setItem('username', data.username);
                checkAuthSession();
                fetchHistory();
            } else {
                switchAuthTab('login');
            }
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error("Auth server error", err);
    }"""

new_handle_auth = """    try {
        let userCred;
        if (authTab === 'register') {
            userCred = await firebase.auth().createUserWithEmailAndPassword(email, pass);
            // Then tell our backend to create profile
            authToken = await userCred.user.getIdToken();
            await fetch('/api/auth/register', {
                method: 'POST',
                headers: getAuthHeaders(),
                body: JSON.stringify({ email: email, username: username })
            });
            showToast("Registration successful");
            closeAuthModal();
            switchAuthTab('login');
        } else {
            // Need email to login in Firebase, if username was provided we assume it was an email.
            // If they typed a username, remind them.
            if (!username.includes('@')) {
                alert("Please use your email address to login");
                return;
            }
            userCred = await firebase.auth().signInWithEmailAndPassword(username, pass);
            authToken = await userCred.user.getIdToken();
            
            showToast("Login successful");
            closeAuthModal();
        }
    } catch (err) {
        alert(err.message);
        console.error("Auth error", err);
    }"""

js_content = js_content.replace(old_handle_auth, new_handle_auth)

# Logout logic
js_content = js_content.replace("""        localStorage.removeItem('user_id');
        localStorage.removeItem('username');
        isAuthed = false;
        checkAuthSession();
        fetchHistory();
        showToast("Logged out successfully");""", """        firebase.auth().signOut().then(() => {
            showToast("Logged out successfully");
        });""")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js_content)
