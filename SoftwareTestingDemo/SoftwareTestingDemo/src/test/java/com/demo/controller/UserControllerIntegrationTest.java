package com.demo.controller;

import com.demo.entity.User;
import org.junit.jupiter.api.Test;
import org.springframework.util.ClassUtils;
import org.springframework.mock.web.MockMultipartFile;
import org.springframework.test.web.servlet.MvcResult;

import java.io.File;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class UserControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRenderSignupPage() throws Exception {
        mockMvc.perform(get("/signup"))
                .andExpect(status().isOk())
                .andExpect(view().name("signup"));
    }

    @Test
    void shouldRenderLoginPage() throws Exception {
        mockMvc.perform(get("/login"))
                .andExpect(status().isOk())
                .andExpect(view().name("login"));
    }

    @Test
    void shouldLoginNormalUserAndStoreSession() throws Exception {
        MvcResult result = mockMvc.perform(post("/loginCheck.do")
                        .param("userID", normalUser.getUserID())
                        .param("password", "pwd1"))
                .andExpect(status().isOk())
                .andExpect(content().string("/index"))
                .andReturn();

        User sessionUser = (User) result.getRequest().getSession().getAttribute("user");
        assertThat(sessionUser.getUserID()).isEqualTo(normalUser.getUserID());
    }

    @Test
    void shouldLoginAdminAndStoreSession() throws Exception {
        MvcResult result = mockMvc.perform(post("/loginCheck.do")
                        .param("userID", adminUser.getUserID())
                        .param("password", "admin"))
                .andExpect(status().isOk())
                .andExpect(content().string("/admin_index"))
                .andReturn();

        User sessionAdmin = (User) result.getRequest().getSession().getAttribute("admin");
        assertThat(sessionAdmin.getUserID()).isEqualTo(adminUser.getUserID());
    }

    @Test
    void shouldRejectInvalidLogin() throws Exception {
        mockMvc.perform(post("/loginCheck.do")
                        .param("userID", normalUser.getUserID())
                        .param("password", "wrong"))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));
    }

    @Test
    void shouldRegisterNewUser() throws Exception {
        mockMvc.perform(post("/register.do")
                        .param("userID", "freshman")
                        .param("userName", "新用户")
                        .param("password", "123456")
                        .param("email", "freshman@mail.com")
                        .param("phone", "13900000000"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("login"));

        User saved = userDao.findByUserID("freshman");
        assertThat(saved).isNotNull();
        assertThat(saved.getIsadmin()).isEqualTo(0);
    }

    @Test
    void shouldNotStoreRegisteredPasswordAsPlainText() throws Exception {
        mockMvc.perform(post("/register.do")
                        .param("userID", "securityUser")
                        .param("userName", "安全测试用户")
                        .param("password", "plain123")
                        .param("email", "security@mail.com")
                        .param("phone", "13900000009"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("login"));

        User saved = userDao.findByUserID("securityUser");
        assertThat(saved.getPassword()).isNotEqualTo("plain123");
    }

    @Test
    void shouldLogoutNormalUser() throws Exception {
        MvcResult result = mockMvc.perform(get("/logout.do").session(userSession()))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/index"))
                .andReturn();

        assertThat(result.getRequest().getSession().getAttribute("user")).isNull();
    }

    @Test
    void shouldLogoutAdmin() throws Exception {
        MvcResult result = mockMvc.perform(get("/quit.do").session(adminSession()))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("/index"))
                .andReturn();

        assertThat(result.getRequest().getSession().getAttribute("admin")).isNull();
    }

    @Test
    void shouldUpdateUserProfile() throws Exception {
        mockMvc.perform(multipart("/updateUser.do")
                        .file(emptyImage("picture"))
                        .session(userSession())
                        .param("userName", "学生一-修改")
                        .param("userID", normalUser.getUserID())
                        .param("passwordNew", "pwd-new")
                        .param("email", "updated@mail.com")
                        .param("phone", "13600000000"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("user_info"))
                .andExpect(request().sessionAttribute("user", userDao.findByUserID(normalUser.getUserID())));

        User updated = userDao.findByUserID(normalUser.getUserID());
        assertThat(updated.getUserName()).isEqualTo("学生一-修改");
        assertThat(updated.getPassword()).isEqualTo("pwd-new");
        assertThat(updated.getEmail()).isEqualTo("updated@mail.com");
    }

    @Test
    void shouldKeepOldPasswordWhenNewPasswordIsBlank() throws Exception {
        mockMvc.perform(multipart("/updateUser.do")
                        .file(emptyImage("picture"))
                        .session(userSession())
                        .param("userName", "学生一-保留密码")
                        .param("userID", normalUser.getUserID())
                        .param("passwordNew", "")
                        .param("email", "keep@mail.com")
                        .param("phone", "13600000001"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("user_info"));

        User updated = userDao.findByUserID(normalUser.getUserID());
        assertThat(updated.getPassword()).isEqualTo("pwd1");
        assertThat(updated.getUserName()).isEqualTo("学生一-保留密码");
    }

    @Test
    void shouldUpdateUserProfileWithPicture() throws Exception {
        mockMvc.perform(multipart("/updateUser.do")
                        .file(new MockMultipartFile("picture", "user.txt", "text/plain", "user-image".getBytes()))
                        .session(userSession())
                        .param("userName", "学生一-头像更新")
                        .param("userID", normalUser.getUserID())
                        .param("passwordNew", "pwd-photo")
                        .param("email", "photo@mail.com")
                        .param("phone", "13600000002"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("user_info"));

        User updated = userDao.findByUserID(normalUser.getUserID());
        assertThat(updated.getPicture()).startsWith("file/user/");
        assertThat(updated.getPassword()).isEqualTo("pwd-photo");
        deleteSavedFile(updated.getPicture());
    }

    @Test
    void shouldCheckPassword() throws Exception {
        mockMvc.perform(get("/checkPassword.do")
                        .param("userID", normalUser.getUserID())
                        .param("password", "pwd1"))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));
    }

    @Test
    void shouldRejectWrongPasswordCheck() throws Exception {
        mockMvc.perform(get("/checkPassword.do")
                        .param("userID", normalUser.getUserID())
                        .param("password", "wrong"))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));
    }

    @Test
    void shouldReturnFalseWhenCheckingPasswordForUnknownUser() throws Exception {
        mockMvc.perform(get("/checkPassword.do")
                        .param("userID", "missing-user")
                        .param("password", "pwd"))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));
    }

    @Test
    void shouldRenderUserInfoPage() throws Exception {
        mockMvc.perform(get("/user_info").session(userSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("user_info"));
    }

    private void deleteSavedFile(String relativePath) {
        File savedFile = new File(ClassUtils.getDefaultClassLoader().getResource("static").getPath(), relativePath);
        assertThat(savedFile).exists();
        assertThat(savedFile.delete()).isTrue();
    }
}
