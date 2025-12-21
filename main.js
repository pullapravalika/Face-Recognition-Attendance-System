// Basic JS for form validation or simple interactions

document.addEventListener("DOMContentLoaded", () => {
    const loginForm = document.querySelector("#loginForm");
    if (loginForm) {
        loginForm.addEventListener("submit", (e) => {
            const username = document.querySelector("#username").value.trim();
            const password = document.querySelector("#password").value.trim();

            if (!username || !password) {
                e.preventDefault();
                alert("Please enter both username and password.");
            }
        });
    }

    const registerForm = document.querySelector("#registerForm");
    if (registerForm) {
        registerForm.addEventListener("submit", (e) => {
            const username = document.querySelector("#username").value.trim();
            const email = document.querySelector("#email").value.trim();
            const password = document.querySelector("#password").value.trim();
            const confirmPassword = document.querySelector("#confirm_password").value.trim();

            if (!username || !email || !password || !confirmPassword) {
                e.preventDefault();
                alert("Please fill all fields.");
                return;
            }

            if (password !== confirmPassword) {
                e.preventDefault();
                alert("Passwords do not match.");
            }
        });
    }
});
