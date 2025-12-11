

    

document.getElementById("login_btn").addEventListener("click",function(e){
    e.preventDefault();

    let username=document.getElementById("username_text").value;
    let password=document.getElementById("password_text").value;
    
    if(username=="Admin" && password=="CE12Mx_553_Pks_FaceBox"){
        alert("✔️ Giriş Başarılı")
        window.location.href="index.html";
    }
    else{
         alert("❌ Kullanıcı adı veya şifre hatalı!");
    }
});

document.getElementById("login_btn").addEventListener("keypress",function(e){   
  
    if(e.key=="Enter"){
        e.preventDefault();
        document.getElementById("login_btn").click();  
        
    }
    else{
        alert("Kullanıcı adı veya şifre hatalı.");
        return;
    }
});
