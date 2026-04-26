package com.demo.controller;

import com.demo.entity.Venue;
import org.junit.jupiter.api.Test;
import org.springframework.util.ClassUtils;
import org.springframework.mock.web.MockMultipartFile;

import java.io.File;

import static org.assertj.core.api.Assertions.assertThat;
import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.multipart;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.model;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.redirectedUrl;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.view;

class AdminVenueControllerIntegrationTest extends AbstractControllerIntegrationTest {
    @Test
    void shouldRenderVenueManagePage() throws Exception {
        mockMvc.perform(get("/venue_manage").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("admin/venue_manage"))
                .andExpect(model().attributeExists("total"));
    }

    @Test
    void shouldRenderVenueEditPage() throws Exception {
        mockMvc.perform(get("/venue_edit").session(adminSession()).param("venueID", String.valueOf(venueA.getVenueID())))
                .andExpect(status().isOk())
                .andExpect(view().name("/admin/venue_edit"))
                .andExpect(model().attributeExists("venue"));
    }

    @Test
    void shouldRenderVenueAddPage() throws Exception {
        mockMvc.perform(get("/venue_add").session(adminSession()))
                .andExpect(status().isOk())
                .andExpect(view().name("/admin/venue_add"));
    }

    @Test
    void shouldReturnVenueList() throws Exception {
        mockMvc.perform(get("/venueList.do").session(adminSession()).param("page", "1"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(2)));
    }

    @Test
    void shouldAddVenueWithoutPicture() throws Exception {
        mockMvc.perform(multipart("/addVenue.do")
                        .file(emptyImage("picture"))
                        .session(adminSession())
                        .param("venueName", "游泳馆")
                        .param("address", "浦东")
                        .param("description", "室内游泳馆")
                        .param("price", "180")
                        .param("open_time", "08:00")
                        .param("close_time", "22:00"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("venue_manage"));

        Venue saved = venueDao.findByVenueName("游泳馆");
        assertThat(saved).isNotNull();
        assertThat(saved.getPicture()).isEmpty();
    }

    @Test
    void shouldAddVenueWithPicture() throws Exception {
        mockMvc.perform(multipart("/addVenue.do")
                        .file(new MockMultipartFile("picture", "venue.txt", "text/plain", "venue-image".getBytes()))
                        .session(adminSession())
                        .param("venueName", "网球馆")
                        .param("address", "徐汇")
                        .param("description", "室外网球场")
                        .param("price", "260")
                        .param("open_time", "09:00")
                        .param("close_time", "21:30"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("venue_manage"));

        Venue saved = venueDao.findByVenueName("网球馆");
        assertThat(saved).isNotNull();
        assertThat(saved.getPicture()).startsWith("file/venue/");
        deleteSavedFile(saved.getPicture());
    }

    @Test
    void shouldModifyVenueWithoutChangingPicture() throws Exception {
        mockMvc.perform(multipart("/modifyVenue.do")
                        .file(emptyImage("picture"))
                        .session(adminSession())
                        .param("venueID", String.valueOf(venueA.getVenueID()))
                        .param("venueName", "羽毛球馆-更新")
                        .param("address", "杨浦")
                        .param("description", "更新描述")
                        .param("price", "150")
                        .param("open_time", "07:00")
                        .param("close_time", "23:00"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("venue_manage"));

        Venue updated = venueDao.findByVenueID(venueA.getVenueID());
        assertThat(updated.getVenueName()).isEqualTo("羽毛球馆-更新");
        assertThat(updated.getPrice()).isEqualTo(150);
    }

    @Test
    void shouldModifyVenueAndChangePicture() throws Exception {
        mockMvc.perform(multipart("/modifyVenue.do")
                        .file(new MockMultipartFile("picture", "updated.txt", "text/plain", "updated-image".getBytes()))
                        .session(adminSession())
                        .param("venueID", String.valueOf(venueA.getVenueID()))
                        .param("venueName", "羽毛球馆-新图")
                        .param("address", "杨浦")
                        .param("description", "更新描述")
                        .param("price", "160")
                        .param("open_time", "06:30")
                        .param("close_time", "22:30"))
                .andExpect(status().is3xxRedirection())
                .andExpect(redirectedUrl("venue_manage"));

        Venue updated = venueDao.findByVenueID(venueA.getVenueID());
        assertThat(updated.getPicture()).startsWith("file/venue/");
        assertThat(updated.getVenueName()).isEqualTo("羽毛球馆-新图");
        deleteSavedFile(updated.getPicture());
    }

    @Test
    void shouldDeleteVenue() throws Exception {
        mockMvc.perform(post("/delVenue.do").session(adminSession()).param("venueID", String.valueOf(venueB.getVenueID())))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));

        assertThat(venueDao.findByVenueID(venueB.getVenueID())).isNull();
    }

    @Test
    void shouldCheckVenueNameAvailability() throws Exception {
        mockMvc.perform(post("/checkVenueName.do").session(adminSession()).param("venueName", venueA.getVenueName()))
                .andExpect(status().isOk())
                .andExpect(content().string("false"));

        mockMvc.perform(post("/checkVenueName.do").session(adminSession()).param("venueName", "全新场馆"))
                .andExpect(status().isOk())
                .andExpect(content().string("true"));
    }

    private void deleteSavedFile(String relativePath) {
        File savedFile = new File(ClassUtils.getDefaultClassLoader().getResource("static").getPath(), relativePath);
        assertThat(savedFile).exists();
        assertThat(savedFile.delete()).isTrue();
    }
}
