"use strict";

// import firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/9.22.2/firebase-app.js";
import {
  getAuth,
  createUserWithEmailAndPassword,
  signInWithEmailAndPassword,
  signOut,
} from "https://www.gstatic.com/firebasejs/9.22.2/firebase-auth.js";

// Your web app's Firebase cinfiguration
const firebaseConfig = {
  apiKey: "AIzaSyDohyRYgT7aFJdnvU1NGjaq1vIHXxifo7A",
  authDomain: "new-gallery-428819.firebaseapp.com",
  projectId: "new-gallery-428819",
  storageBucket: "new-gallery-428819.appspot.com",
  messagingSenderId: "618130021688",
  appId: "1:618130021688:web:92d52ea3846aef00ac75cd",
};

window.addEventListener("load", function () {
  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  updateUI(this.document.cookie);

  // signup of a new user to firebase
  this.document
    .getElementById("sign-up")
    .addEventListener("click", function () {
      const email = document.getElementById("email").value;
      const password = document.getElementById("password").value;

      createUserWithEmailAndPassword(auth, email, password)
        .then((userCredential) => {
          // we have created as user
          const user = userCredential.user;

          // get the id token for the user who just logged in and force a redirect to /
          user.getIdToken().then((token) => {
            document.cookie = "token=" + token + ";path=/;SameSite=Strict";
            window.location = "/";
          });
        })
        .catch((error) => {
          // issue with signup that we will drop to the console
          console.log(error.code + error.message);
        });
    });

  // login of a user to firebase
  this.document.getElementById("login").addEventListener("click", function () {
    const email = document.getElementById("email").value;
    const password = document.getElementById("password").value;

    signInWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        // we have a signed in user
        const user = userCredential.user;

        // get the ID token of the user who just logged in and force a redirect to /
        user.getIdToken().then((token) => {
          document.cookie = "token=" + token + ";path=/;SameSite=Strict";
          window.location = "/";
        });
      })
      .catch((error) => {
        // issue with signup that we will drop to console
        console.log(error.code + error.message);
      });
  });

  // signout from firebase
  this.document
    .getElementById("sign-out")
    .addEventListener("click", function () {
      signOut(auth).then((output) => {
        // remove the ID token for the user and force a redirect to /
        document.cookie = "token=;path=/;SameSite=Strict";
        window.location = "/";
      });
    });
});

// function will update the UI for the user depending on if they are logged in or notby checking the passed in cookie
// that contains the token
function updateUI(cookie) {
  var token = parseCookieToken(cookie);

  // if a user is logged in, the disable the email, password, signup and login UI elements and show the signout button and
  // vice versa
  if (token.length > 0) {
    document.getElementById("login-box").hidden = true;
    document.getElementById("sign-out").hidden = false;
  } else {
    document.getElementById("login-box").hidden = false;
    document.getElementById("sign-out").hidden = true;
  }
}

function parseCookieToken(cookie) {
  // split the cookie out on the basis of the semi colon
  var strings = cookie.split(";");

  // go through each of the strings
  for (let i = 0; i < strings.length; i++) {
    // split the string based on the = sign. if the LHS is token the return the RHS immediately
    var temp = strings[i].split("=");
    if (temp[0].trim() == "token") return temp[1].trim();
  }

  //   if we got to this point and the token wasn't in the cookie so return the empty string
  return "";
}
