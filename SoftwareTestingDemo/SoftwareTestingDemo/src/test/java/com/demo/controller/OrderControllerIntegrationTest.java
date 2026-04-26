package com.demo.controller;

import com.demo.entity.Order;
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
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.request;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class OrderControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRequireLoginForOrderManage() {
        assertThatThrownBy(() -> mockMvc.perform(get("/order_manage")))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldRenderOrderManageForLoggedUser() throws Exception {
        mockMvc.perform(get("/order_manage").session(userSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("order_manage"))
                .andExpect(model().attributeExists("total"));
    }

    @Test
    void shouldRenderOrderPlacePageWithVenue() throws Exception {
        mockMvc.perform(get("/order_place.do").param("venueID", String.valueOf(venueA.getVenueID())))
                .andExpect(status().isOk())
                .andExpect(view().name("order_place"))
                .andExpect(model().attributeExists("venue"));
    }

    @Test
    void shouldRenderBlankOrderPlacePage() throws Exception {
        mockMvc.perform(get("/order_place"))
                .andExpect(status().isOk())
                .andExpect(view().name("order_place"));
    }

    @Test
    void shouldReturnLoggedUserOrdersOnly() throws Exception {
        mockMvc.perform(get("/getOrderList.do").session(userSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].userID").value(normalUser.getUserID()))
                .andExpect(jsonPath("$[1].userID").value(normalUser.getUserID()));
    }

    @Test
    void shouldRequireLoginForOrderListApi() {
        assertThatThrownBy(() -> mockMvc.perform(get("/getOrderList.do").param("page", "1")))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldCreateOrderAndRedirect() throws Exception {
        mockMvc.perform(post("/addOrder.do")
                        .session(userSession())
                        .param("venueName", venueA.getVenueName())
                        .param("date", "ignored-by-controller")
                        .param("startTime", "2026-05-01 10:00")
                        .param("hours", "3"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("order_manage"));

        Order created = orderDao.findAll().stream()
                .filter(order -> order.getUserID().equals(normalUser.getUserID()) && order.getStartTime().equals(java.time.LocalDateTime.of(2026, 5, 1, 10, 0)))
                .findFirst()
                .orElse(null);
        assertThat(created).isNotNull();
        assertThat(created.getState()).isEqualTo(1);
        assertThat(created.getTotal()).isEqualTo(300);
    }

    @Test
    void shouldRequireLoginWhenCreatingOrder() {
        assertThatThrownBy(() -> mockMvc.perform(post("/addOrder.do")
                        .param("venueName", venueA.getVenueName())
                        .param("date", "ignored-by-controller")
                        .param("startTime", "2026-05-01 10:00")
                        .param("hours", "3")))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldRejectNegativeOrderHours() throws Exception {
        mockMvc.perform(post("/addOrder.do")
                        .session(userSession())
                        .param("venueName", venueA.getVenueName())
                        .param("date", "2026-04-20")
                        .param("startTime", "2026-04-20 10:00")
                        .param("hours", "-1"))
                .andExpect(status().is4xxClientError());
    }

    @Test
    void shouldFinishOrder() throws Exception {
        mockMvc.perform(post("/finishOrder.do")
                        .session(userSession())
                        .param("orderID", String.valueOf(approvedOrder.getOrderID())))
                .andExpect(status().isOk());

        assertThat(orderDao.findByOrderID(approvedOrder.getOrderID()).getState()).isEqualTo(3);
    }

    @Test
    void shouldRenderOrderEditPage() throws Exception {
        mockMvc.perform(get("/modifyOrder.do")
                        .session(userSession())
                        .param("orderID", String.valueOf(approvedOrder.getOrderID())))
                .andExpect(status().isOk())
                .andExpect(view().name("order_edit"))
                .andExpect(model().attributeExists("venue", "order"));
    }

    @Test
    void shouldModifyOrderAndRedirect() throws Exception {
        mockMvc.perform(post("/modifyOrder")
                        .session(userSession())
                        .param("venueName", venueB.getVenueName())
                        .param("date", "ignored")
                        .param("startTime", "2026-05-03 14:00")
                        .param("hours", "4")
                        .param("orderID", String.valueOf(approvedOrder.getOrderID())))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("order_manage"));

        Order updated = orderDao.findByOrderID(approvedOrder.getOrderID());
        assertThat(updated.getVenueID()).isEqualTo(venueB.getVenueID());
        assertThat(updated.getHours()).isEqualTo(4);
        assertThat(updated.getState()).isEqualTo(1);
        assertThat(updated.getTotal()).isEqualTo(800);
    }

    @Test
    void shouldRequireLoginWhenModifyingOrder() {
        assertThatThrownBy(() -> mockMvc.perform(post("/modifyOrder")
                        .param("venueName", venueB.getVenueName())
                        .param("date", "ignored")
                        .param("startTime", "2026-05-03 14:00")
                        .param("hours", "4")
                        .param("orderID", String.valueOf(approvedOrder.getOrderID()))))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldDeleteOrder() throws Exception {
        mockMvc.perform(post("/delOrder.do")
                        .session(userSession())
                        .param("orderID", String.valueOf(pendingOrder.getOrderID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(orderDao.findByOrderID(pendingOrder.getOrderID())).isNull();
    }

    @Test
    void shouldRejectDeletingOrderWithoutLogin() {
        assertThatThrownBy(() -> mockMvc.perform(post("/delOrder.do")
                        .param("orderID", String.valueOf(pendingOrder.getOrderID()))))
                .isInstanceOf(NestedServletException.class)
                .hasCauseInstanceOf(LoginException.class);
    }

    @Test
    void shouldReturnVenueOrdersByDate() throws Exception {
        mockMvc.perform(get("/order/getOrderList.do")
                        .param("venueName", venueA.getVenueName())
                        .param("date", "2026-04-20"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.venue.venueName").value("羽毛球馆"))
                .andExpect(jsonPath("$.orders", hasSize(1)))
                .andExpect(jsonPath("$.orders[0].orderID").value(pendingOrder.getOrderID()));
    }
}
