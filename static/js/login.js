


var flag_admin = "{{ session['admin'] }}";

if (flag_admin == "True") {
    document.getElementById('left_contents').classList.add("dimmed")
    document.getElementById('right_contents').classList.add("dimmed")
    document.getElementById('overlay_contents').style.display = 'flex';
} else {
    console.log("False");
}

function closeOverlay() {
    document.querySelector('.overlay').style.display = 'none';
    document.querySelectorAll('.dimmed').forEach(el => el.classList.remove('dimmed'));
}
