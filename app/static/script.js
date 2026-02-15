document.getElementById("userForm").addEventListener("submit", function (e) {
    e.preventDefault(); // stop page refresh

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;

    fetch("/login", {
    method: "POST",
    headers: {
        "Content-Type": "application/json"
    },
    body: JSON.stringify({
        email: email,
        password: password
    })
    })
    .then(res => res.json())
    .then(data => {
    if (data.success) {
        window.location.href = "/dashboard";
    } else {
        alert(data.message);
    }
    });

});
