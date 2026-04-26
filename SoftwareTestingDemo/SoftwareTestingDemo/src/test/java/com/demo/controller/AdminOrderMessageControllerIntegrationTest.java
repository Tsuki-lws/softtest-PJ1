package com.demo.controller;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class AdminOrderMessageControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRenderReservationManagePage() throws Exception {
        mockMvc.perform(get("/reservation_manage").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/reservation_manage"))
                .andExpect(model().attributeExists("order_list", "total"));
    }

    @Test
    void shouldReturnPendingOrdersForAudit() throws Exception {
        mockMvc.perform(get("/admin/getOrderList.do").session(adminSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].orderID").value(pendingOrder.getOrderID()));
    }

    @Test
    void shouldApproveOrder() throws Exception {
        mockMvc.perform(post("/passOrder.do").session(adminSession()).param("orderID", String.valueOf(pendingOrder.getOrderID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(orderDao.findByOrderID(pendingOrder.getOrderID()).getState()).isEqualTo(2);
    }

    @Test
    void shouldRejectOrder() throws Exception {
        mockMvc.perform(post("/rejectOrder.do").session(adminSession()).param("orderID", String.valueOf(pendingOrder.getOrderID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(orderDao.findByOrderID(pendingOrder.getOrderID()).getState()).isEqualTo(4);
    }

    @Test
    void shouldRenderAdminMessageManagePage() throws Exception {
        mockMvc.perform(get("/message_manage").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/message_manage"))
                .andExpect(model().attributeExists("total"));
    }

    @Test
    void shouldReturnPendingMessagesForAudit() throws Exception {
        mockMvc.perform(get("/messageList.do").session(adminSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(1)))
                .andExpect(jsonPath("$[0].messageID").value(pendingMessage.getMessageID()));
    }

    @Test
    void shouldApproveMessage() throws Exception {
        mockMvc.perform(post("/passMessage.do").session(adminSession()).param("messageID", String.valueOf(pendingMessage.getMessageID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(messageDao.findByMessageID(pendingMessage.getMessageID()).getState()).isEqualTo(2);
    }

    @Test
    void shouldRejectMessage() throws Exception {
        mockMvc.perform(post("/rejectMessage.do").session(adminSession()).param("messageID", String.valueOf(pendingMessage.getMessageID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(messageDao.findByMessageID(pendingMessage.getMessageID()).getState()).isEqualTo(3);
    }

    @Test
    void shouldDeleteMessageByAdminEndpoint() throws Exception {
        mockMvc.perform(get("/delMessage.do").session(adminSession()).param("messageID", String.valueOf(pendingMessage.getMessageID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(messageDao.findByMessageID(pendingMessage.getMessageID())).isNull();
    }
}
