// MIT License

// Copyright (c) 2017 kirk25

// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:

// The above copyright notice and this permission notice shall be included in
// all copies or substantial portions of the Software.

// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

$(function(){
    // Initialize Firebase
    var config = {
        apiKey: "AIzaSyBe3opjJNehnKnZZK1KZErF5h72Pllb-r4",
        authDomain: "nest-thermostat-history.firebaseapp.com",
        projectId: "nest-thermostat-history",
    };

    // This is passed into the backend to authenticate the user.
    var userIdToken = null;

    // Firebase log-in
    function configureFirebaseLogin() {

        firebase.initializeApp(config);

        firebase.auth().onAuthStateChanged(function(user) {
            if (user) {
                $('#logged-out').hide();
                var name = user.displayName;

                /* If the provider gives a display name, use the name for the
                   personal welcome message. Otherwise, use the user's email. */
                var welcomeName = name ? name : user.email;

                user.getToken().then(function(idToken) {
                    userIdToken = idToken;

                    $('#user').text(welcomeName);
                    $('#logged-in').show();

                });

            } else {
                $('#logged-in').hide();
                $('#logged-out').show();

            }

        });

    }

    // Firebase log-in widget
    function configureFirebaseLoginWidget() {
        var uiConfig = {
            'signInSuccessUrl': '/',
            'signInOptions': [
                firebase.auth.GoogleAuthProvider.PROVIDER_ID,
                // firebase.auth.FacebookAuthProvider.PROVIDER_ID,
                // firebase.auth.TwitterAuthProvider.PROVIDER_ID,
                // firebase.auth.GithubAuthProvider.PROVIDER_ID,
                // firebase.auth.EmailAuthProvider.PROVIDER_ID
            ],
            // Terms of service url
            // TODO: get an actual ToS URL  
            'tosUrl': 'http://www.example.com',
        };

        var ui = new firebaseui.auth.AuthUI(firebase.auth());
        ui.start('#firebaseui-auth-container', uiConfig);
    }

    // Sign out a user
    var signOutBtn =$('#sign-out');
    signOutBtn.click(function(event) {
        event.preventDefault();

        firebase.auth().signOut().then(function() {
            console.log("Sign out successful");
        }, function(error) {
            console.log(error);
        });
    });

    configureFirebaseLogin();
    configureFirebaseLoginWidget();

});
