document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('loginForm');

    if (loginForm) {
        loginForm.addEventListener('submit', (event) => {
            // Prevent the default form submission which reloads the page
            event.preventDefault();

            // Get the values from the form fields
            const email = document.getElementById('email').value;
            const password = document.getElementById('password').value;

            // Simple validation
            if (email === '' || password === '') {
                alert('Please fill in both email and password.');
                return;
            }

            // For now, we'll just log the data to the console.
            // In a real application, you would send this to a server.
            console.log('Form Submitted');
            console.log('Email:', email);
            console.log('Password:', password); // Note: Never log passwords in a real production app!

            alert(`Login attempt with email: ${email}`);
            
            // Here you would typically make a fetch() call to your login API
        });
    }
});