package com.demo.controller;

import com.demo.entity.User;
import com.demo.exception.LoginException;
import org.junit.jupiter.api.Test;
import org.springframework.web.util.NestedServletException;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class AdminUserControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRejectUnauthenticatedAdminPageAccess() {
        assertThatThrownBy(() -> mockMvc.perform(get("/user_manage")))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldRenderUserManagePage() throws Exception {
        mockMvc.perform(get("/user_manage").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/user_manage"))
                .andExpect(model().attributeExists("total"));
    }

    @Test
    void shouldRenderUserAddPage() throws Exception {
        mockMvc.perform(get("/user_add").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/user_add"));
    }

    @Test
    void shouldReturnNormalUsersOnly() throws Exception {
        mockMvc.perform(get("/userList.do").session(adminSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].isadmin").value(0))
                .andExpect(jsonPath("$[1].isadmin").value(0));
    }

    @Test
    void shouldRenderUserEditPage() throws Exception {
        mockMvc.perform(get("/user_edit").session(adminSession()).param("id", String.valueOf(normalUser.getId())))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/user_edit"))
                .andExpect(model().attributeExists("user"));
    }

    @Test
    void shouldModifyUserAndRedirect() throws Exception {
        mockMvc.perform(post("/modifyUser.do")
                        .session(adminSession())
                        .param("userID", "student1-new")
                        .param("oldUserID", normalUser.getUserID())
                        .param("userName", "学生一-后台修改")
                        .param("password", "new-password")
                        .param("email", "backend@mail.com")
                        .param("phone", "13500000000"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("user_manage"));

        User updated = userDao.findByUserID("student1-new");
        assertThat(updated).isNotNull();
        assertThat(updated.getUserName()).isEqualTo("学生一-后台修改");
    }

    @Test
    void shouldAddUserAndRedirect() throws Exception {
        mockMvc.perform(post("/addUser.do")
                        .session(adminSession())
                        .param("userID", "student3")
                        .param("userName", "学生三")
                        .param("password", "pwd3")
                        .param("email", "student3@mail.com")
                        .param("phone", "13300000000"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("user_manage"));

        assertThat(userDao.findByUserID("student3")).isNotNull();
    }

    @Test
    void shouldCheckUserIdAvailability() throws Exception {
        mockMvc.perform(post("/checkUserID.do").session(adminSession()).param("userID", normalUser.getUserID()))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));

        mockMvc.perform(post("/checkUserID.do").session(adminSession()).param("userID", "brandNew"))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));
    }

    @Test
    void shouldDeleteUser() throws Exception {
        mockMvc.perform(post("/delUser.do").session(adminSession()).param("id", String.valueOf(anotherUser.getId())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(userDao.findById(anotherUser.getId())).isNull();
    }
}
