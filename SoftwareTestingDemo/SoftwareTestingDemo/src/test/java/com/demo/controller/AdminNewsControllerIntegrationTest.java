package com.demo.controller;

import com.demo.entity.News;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class AdminNewsControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRenderNewsManagePage() throws Exception {
        mockMvc.perform(get("/news_manage").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/news_manage"))
                .andExpect(model().attributeExists("total"));
    }

    @Test
    void shouldRenderNewsAddPage() throws Exception {
        mockMvc.perform(get("/news_add").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("/admin/news_add"));
    }

    @Test
    void shouldRenderNewsEditPage() throws Exception {
        mockMvc.perform(get("/news_edit").session(adminSession()).param("newsID", String.valueOf(newerNews.getNewsID())))
                .andExpect(status().isOk())
                .andExpect(view().name("/admin/news_edit"))
                .andExpect(model().attributeExists("news"));
    }

    @Test
    void shouldReturnPagedNewsList() throws Exception {
        mockMvc.perform(get("/newsList.do").session(adminSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)))
                .andExpect(jsonPath("$[0].title").value("新通知"));
    }

    @Test
    void shouldDeleteNews() throws Exception {
        mockMvc.perform(post("/delNews.do").session(adminSession()).param("newsID", String.valueOf(olderNews.getNewsID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(newsDao.findById(olderNews.getNewsID()).isPresent()).isFalse();
    }

    @Test
    void shouldModifyNewsAndRedirect() throws Exception {
        mockMvc.perform(post("/modifyNews.do")
                        .session(adminSession())
                        .param("newsID", String.valueOf(newerNews.getNewsID()))
                        .param("title", "新闻已更新")
                        .param("content", "更新后的内容"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("news_manage"));

        News updated = newsDao.findById(newerNews.getNewsID()).orElseThrow(IllegalStateException::new);
        assertThat(updated.getTitle()).isEqualTo("新闻已更新");
    }

    @Test
    void shouldAddNewsAndRedirect() throws Exception {
        mockMvc.perform(post("/addNews.do")
                        .session(adminSession())
                        .param("title", "新增新闻")
                        .param("content", "新增内容"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("news_manage"));

        assertThat(newsDao.findAll().stream().anyMatch(news -> "新增新闻".equals(news.getTitle()))).isTrue();
    }
}
