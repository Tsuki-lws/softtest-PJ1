package com.demo.defect;

import com.demo.controller.AbstractControllerIntegrationTest;
import com.demo.entity.User;
import com.demo.exception.LoginException;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

class DefectExplorationCases extends AbstractControllerIntegrationTest {
    @Test
    @DisplayName("后台管理页未登录时应拒绝访问")
    void shouldRejectUnauthenticatedAdminPageAccess() {
        assertThatThrownBy(() -> mockMvc.perform(get("/user_manage")))
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    @DisplayName("不存在的用户进行密码校验时应返回 false")
    void shouldReturnFalseWhenCheckingPasswordForUnknownUser() throws Exception {
        mockMvc.perform(get("/checkPassword.do")
                        .param("userID", "missing-user")
                        .param("password", "pwd"))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));
    }

    @Test
    @DisplayName("分页参数 page=0 时不应导致服务端异常")
    void shouldHandleZeroPageNumberGracefully() throws Exception {
        mockMvc.perform(get("/news/getNewsList").param("page", "0"))
                .andExpect(status().isOk());
    }

    @Test
    @DisplayName("未登录用户不应能删除订单")
    void shouldRejectDeletingOrderWithoutLogin() {
        assertThatThrownBy(() -> mockMvc.perform(post("/delOrder.do")
                        .param("orderID", String.valueOf(pendingOrder.getOrderID()))))
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    @DisplayName("注册密码不应以明文存储")
    void shouldNotStoreRegisteredPasswordAsPlainText() throws Exception {
        mockMvc.perform(post("/register.do")
                        .param("userID", "securityUser")
                        .param("userName", "安全测试用户")
                        .param("password", "plain123")
                        .param("email", "security@mail.com")
                        .param("phone", "13900000009"))
                .andExpect(status().is3xxRedirection());

        User saved = userDao.findByUserID("securityUser");

        assertThat(saved.getPassword()).isNotEqualTo("plain123");
    }

    @Test
    @DisplayName("预约时长为负数时应拒绝提交")
    void shouldRejectNegativeOrderHours() throws Exception {
        mockMvc.perform(post("/addOrder.do")
                        .session(userSession())
                        .param("venueName", venueA.getVenueName())
                        .param("date", "2026-04-20")
                        .param("startTime", "2026-04-20 10:00")
                        .param("hours", "-1"))
                .andExpect(status().is4xxClientError());
    }
}
