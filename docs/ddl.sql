CREATE TABLE `domain`
(
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id` CHAR(32)     NOT NULL,
    `name`         VARCHAR(255) NOT NULL,
    `created_at`   DATETIME     NOT NULL,
    `updated_at`   DATETIME     NOT NULL,
    `deleted_at`   DATETIME,
    PRIMARY KEY (`id`)
);

CREATE TABLE `project`
(
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id` CHAR(32)     NOT NULL,
    `domain_id`    BIGINT       NOT NULL,
    `name`         VARCHAR(255) NOT NULL,
    `created_at`   DATETIME     NOT NULL,
    `updated_at`   DATETIME     NOT NULL,
    `deleted_at`   DATETIME,
    `version`      INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`domain_id`) REFERENCES domain (`id`)
);

CREATE TABLE `user`
(
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id` CHAR(32)     NOT NULL,
    `domain_id`    BIGINT       NOT NULL,
    `account_id`   VARCHAR(20)  NOT NULL,
    `name`         VARCHAR(15)  NOT NULL,
    `password`     VARCHAR(255) NOT NULL,
    `created_at`   DATETIME     NOT NULL,
    `updated_at`   DATETIME     NOT NULL,
    `deleted_at`   DATETIME,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`domain_id`) REFERENCES `domain` (`id`)
);

CREATE TABLE `project_user`
(
    `id`         BIGINT   NOT NULL AUTO_INCREMENT,
    `user_id`    BIGINT   NOT NULL,
    `project_id` BIGINT   NOT NULL,
    `created_at` DATETIME NOT NULL,
    `updated_at` DATETIME NOT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
);

CREATE TABLE `server`
(
    `id`                  BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id`        CHAR(36)     NOT NULL,
    `project_id`          BIGINT       NOT NULL,
    `flavor_openstack_id` CHAR(36)     NOT NULL,
    `name`                VARCHAR(255) NOT NULL,
    `description`         VARCHAR(255) NOT NULL,
    `status`              VARCHAR(30)  NOT NULL,
    `created_at`          DATETIME     NOT NULL,
    `updated_at`          DATETIME     NOT NULL,
    `deleted_at`          DATETIME,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
);

CREATE TABLE `network_interface`
(
    `id`               BIGINT      NOT NULL AUTO_INCREMENT,
    `server_id`        BIGINT      NULL,
    `project_id`       BIGINT      NOT NULL,
    `openstack_id`     CHAR(36)    NOT NULL,
    `fixed_ip_address` VARCHAR(15) NOT NULL,
    `created_at`       DATETIME    NOT NULL,
    `updated_at`       DATETIME    NOT NULL,
    `deleted_at`       DATETIME,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
    FOREIGN KEY (`server_id`) REFERENCES `server` (`id`)
);

CREATE TABLE `volume`
(
    `id`                       BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id`             CHAR(36)     NOT NULL,
    `project_id`               BIGINT       NOT NULL,
    `server_id`                BIGINT       NULL,
    `volume_type_openstack_id` CHAR(36)     NOT NULL,
    `image_openstack_id`       CHAR(36)     NULL,
    `name`                     VARCHAR(255) NOT NULL,
    `description`              VARCHAR(255) NOT NULL,
    `status`                   VARCHAR(30)  NOT NULL,
    `size`                     INT          NOT NULL,
    `is_root_volume`           TINYINT(1)   NOT NULL,
    `created_at`               DATETIME     NOT NULL,
    `updated_at`               DATETIME     NOT NULL,
    `deleted_at`               DATETIME,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
    FOREIGN KEY (`server_id`) REFERENCES `server` (`id`)
);

CREATE TABLE `security_group`
(
    `id`           BIGINT       NOT NULL AUTO_INCREMENT,
    `openstack_id` CHAR(36)     NOT NULL,
    `project_id`   BIGINT       NOT NULL,
    `name`         VARCHAR(255) NOT NULL,
    `description`  VARCHAR(255) NULL,
    `created_at`   DATETIME     NOT NULL,
    `updated_at`   DATETIME     NOT NULL,
    `deleted_at`   DATETIME,
    `version`      INT          NOT NULL DEFAULT 0,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`)
);

CREATE TABLE `network_interface_security_group`
(
    `id`                   BIGINT   NOT NULL AUTO_INCREMENT,
    `network_interface_id` BIGINT   NOT NULL,
    `security_group_id`    BIGINT   NOT NULL,
    `created_at`           DATETIME NOT NULL,
    `updated_at`           DATETIME NOT NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`network_interface_id`) REFERENCES `network_interface` (`id`),
    FOREIGN KEY (`security_group_id`) REFERENCES `security_group` (`id`)
);

CREATE TABLE `floating_ip`
(
    `id`                   BIGINT      NOT NULL AUTO_INCREMENT,
    `openstack_id`         CHAR(36)    NOT NULL,
    `project_id`           BIGINT      NOT NULL,
    `network_interface_id` BIGINT      NULL,
    `status`               VARCHAR(30) NOT NULL,
    `address`              VARCHAR(15) NOT NULL,
    `created_at`           DATETIME    NOT NULL,
    `updated_at`           DATETIME    NOT NULL,
    `deleted_at`           DATETIME    NULL,
    PRIMARY KEY (`id`),
    FOREIGN KEY (`project_id`) REFERENCES `project` (`id`),
    FOREIGN KEY (`network_interface_id`) REFERENCES `network_interface` (`id`)
);