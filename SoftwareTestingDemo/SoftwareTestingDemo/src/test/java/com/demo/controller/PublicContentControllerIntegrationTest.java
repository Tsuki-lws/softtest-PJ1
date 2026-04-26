package com.demo.controller;

import org.junit.jupiter.api.Test;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class PublicContentControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRenderIndexPageWithAggregatedContent() throws Exception {
        mockMvc.perform(get("/index"))
                .andExpect(status().isOk())
                .andExpect(view().name("index"))
                .andExpect(model().attributeExists("news_list", "venue_list", "message_list"));
    }

    @Test
    void shouldRenderAdminIndexPage() throws Exception {
        mockMvc.perform(get("/admin_index"))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/admin_index"));
    }

    @Test
    void shouldRenderNewsDetailPage() throws Exception {
        mockMvc.perform(get("/news").param("newsID", String.valueOf(newerNews.getNewsID())))
                .andExpect(status().isOk())
                .andExpect(view().name("news"))
                .andExpect(model().attributeExists("news"));
    }

    @Test
    void shouldReturnPagedNewsJson() throws Exception {
        mockMvc.perform(get("/news/getNewsList").param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.content[0].title").value("新通知"))
                .andExpect(jsonPath("$.content[1].title").value("旧通知"));
    }

    @Test
    void shouldUseDefaultPageWhenNewsPageParamMissing() throws Exception {
        mockMvc.perform(get("/news/getNewsList"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.content[0].title").value("新通知"));
    }

    @Test
    void shouldHandleZeroPageNumberGracefully() throws Exception {
        mockMvc.perform(get("/news/getNewsList").param("page", "0"))
                .andExpect(status().isOk());
    }

    @Test
    void shouldRenderNewsListPage() throws Exception {
        mockMvc.perform(get("/news_list"))
                .andExpect(status().isOk())
                .andExpect(view().name("news_list"))
                .andExpect(model().attributeExists("news_list", "total"));
    }

    @Test
    void shouldRenderVenueDetailPage() throws Exception {
        mockMvc.perform(get("/venue").param("venueID", String.valueOf(venueA.getVenueID())))
                .andExpect(status().isOk())
                .andExpect(view().name("venue"))
                .andExpect(model().attributeExists("venue"));
    }

    @Test
    void shouldReturnPagedVenueJson() throws Exception {
        mockMvc.perform(get("/venuelist/getVenueList").param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(2)))
                .andExpect(jsonPath("$.content[0].venueName").value("羽毛球馆"))
                .andExpect(jsonPath("$.content[1].venueName").value("篮球馆"));
    }

    @Test
    void shouldReturnEmptyVenuePageWhenPageExceedsBoundary() throws Exception {
        mockMvc.perform(get("/venuelist/getVenueList").param("page", "2"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.content", hasSize(0)));
    }

    @Test
    void shouldRenderVenueListPage() throws Exception {
        mockMvc.perform(get("/venue_list"))
                .andExpect(status().isOk())
                .andExpect(view().name("venue_list"))
                .andExpect(model().attributeExists("venue_list", "total"));
    }
}
