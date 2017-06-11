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
