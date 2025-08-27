// dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    console.log("MindPal Dashboard Ready");

    // Add hover effect to explore cards
    const cards = document.querySelectorAll(".explore-card");
    cards.forEach(card => {
        card.addEventListener("mouseenter", () => {
            card.style.boxShadow = "0 12px 24px rgba(0, 0, 0, 0.3)";
        });
        card.addEventListener("mouseleave", () => {
            card.style.boxShadow = "0 8px 16px rgba(0, 0, 0, 0.2)";
        });
    });
});

// dashboard.js

document.addEventListener("DOMContentLoaded", () => {
    const loginLink = document.getElementById("login-link");
    const userMenu = document.getElementById("user-menu");
    const logoutBtn = document.getElementById("logout-btn");

    // Simulate login: check localStorage
    const isLoggedIn = localStorage.getItem("isLoggedIn") === "true";

    if (isLoggedIn) {
        loginLink.style.display = "none";
        userMenu.style.display = "inline-block";
    } else {
        loginLink.style.display = "inline-block";
        userMenu.style.display = "none";
    }

    // Fake logout
    logoutBtn.addEventListener("click", (e) => {
        e.preventDefault();
        localStorage.setItem("isLoggedIn", "false");
        window.location.reload();
    });
});
