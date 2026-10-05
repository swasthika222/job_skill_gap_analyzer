document.addEventListener(
    "DOMContentLoaded",
    function () {

        // Auto-hide flash messages

        const messages =
            document.querySelectorAll(".flash");

        messages.forEach(function (message) {

            setTimeout(function () {

                message.style.opacity = "0";

                setTimeout(function () {

                    message.remove();

                }, 500);

            }, 4000);

        });


        // Password confirmation

        const registerForm =
            document.querySelector(
                'form[action*="register"]'
            );

        if (registerForm) {

            registerForm.addEventListener(
                "submit",
                function (event) {

                    const password =
                        document.querySelector(
                            'input[name="password"]'
                        );

                    const confirmPassword =
                        document.querySelector(
                            'input[name="confirm_password"]'
                        );

                    if (
                        password &&
                        confirmPassword &&
                        password.value !==
                        confirmPassword.value
                    ) {

                        event.preventDefault();

                        alert(
                            "Passwords do not match."
                        );

                    }

                }
            );

        }

    }
);