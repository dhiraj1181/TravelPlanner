package com.traveller.demo.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.web.client.RestTemplate;

/**
 * RestTemplateConfig - RestTemplate with explicit timeouts for the ML Engine.
 *
 * connectTimeout: 5 s  – give up if the ML engine process is not even running
 * readTimeout:   60 s  – ML engine may need ~30 s to hit Overpass API for a
 *                        new city; 60 s gives plenty of headroom.
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(5_000);   // 5 seconds to establish connection
        factory.setReadTimeout(60_000);     // 60 seconds to receive full response
        return new RestTemplate(factory);
    }
}
