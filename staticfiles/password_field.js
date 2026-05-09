function togglePassword(inputId, iconElement) {
    const passwordInput = document.getElementById(inputId);
    const passwordType = passwordInput.type;
        
    passwordInput.type = (passwordType === 'password') ? 'text' : 'password';

    const eyeOpen = iconElement.getAttribute('data-eye-open');
    const eyeClose = iconElement.getAttribute('data-eye-close');
        
    iconElement.src = (passwordType === 'password') ? eyeClose : eyeOpen;
}
