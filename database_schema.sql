CREATE INDEX "auth_group_permissions_group_id_b120cbf9" ON "auth_group_permissions" ("group_id");

CREATE UNIQUE INDEX "auth_group_permissions_group_id_permission_id_0cd325b0_uniq" ON "auth_group_permissions" ("group_id", "permission_id");

CREATE INDEX "auth_group_permissions_permission_id_84c5c92e" ON "auth_group_permissions" ("permission_id");

CREATE INDEX "auth_permission_content_type_id_2f476e4b" ON "auth_permission" ("content_type_id");

CREATE UNIQUE INDEX "auth_permission_content_type_id_codename_01ab375a_uniq" ON "auth_permission" ("content_type_id", "codename");

CREATE INDEX "auth_user_groups_group_id_97559544" ON "auth_user_groups" ("group_id");

CREATE INDEX "auth_user_groups_user_id_6a12ed8b" ON "auth_user_groups" ("user_id");

CREATE UNIQUE INDEX "auth_user_groups_user_id_group_id_94350c0c_uniq" ON "auth_user_groups" ("user_id", "group_id");

CREATE INDEX "auth_user_user_permissions_permission_id_1fbb5f2c" ON "auth_user_user_permissions" ("permission_id");

CREATE INDEX "auth_user_user_permissions_user_id_a95ead1b" ON "auth_user_user_permissions" ("user_id");

CREATE UNIQUE INDEX "auth_user_user_permissions_user_id_permission_id_14a6b632_uniq" ON "auth_user_user_permissions" ("user_id", "permission_id");

CREATE INDEX "django_admin_log_content_type_id_c4bce8eb" ON "django_admin_log" ("content_type_id");

CREATE INDEX "django_admin_log_user_id_c564eba6" ON "django_admin_log" ("user_id");

CREATE UNIQUE INDEX "django_content_type_app_label_model_76bd3d3b_uniq" ON "django_content_type" ("app_label", "model");

CREATE INDEX "django_session_expire_date_a5c62663" ON "django_session" ("expire_date");

CREATE INDEX "tracking_bus_current_stop_time_id_da365771" ON "tracking_bus" ("current_stop_time_id");

CREATE INDEX "tracking_bus_current_trip_id_28a4f1b6" ON "tracking_bus" ("current_trip_id");

CREATE INDEX "tracking_driverbusassignment_bus_id_362ebfb2" ON "tracking_driverbusassignment" ("bus_id");

CREATE INDEX "tracking_driverbusassignment_driver_id_7b5bb062" ON "tracking_driverbusassignment" ("driver_id");

CREATE INDEX "tracking_stoptime_stop_id_28387368" ON "tracking_stoptime" ("stop_id");

CREATE INDEX "tracking_stoptime_trip_id_c69b3acf" ON "tracking_stoptime" ("trip_id");

CREATE INDEX "tracking_trip_route_id_72abf77e" ON "tracking_trip" ("route_id");

CREATE INDEX "tracking_waitingrequest_passenger_id_e4aa51d1" ON "tracking_waitingrequest" ("passenger_id");

CREATE INDEX "tracking_waitingrequest_stop_id_3b659d17" ON "tracking_waitingrequest" ("stop_id");

CREATE INDEX "tracking_waitingrequest_trip_id_2c1bf5f8" ON "tracking_waitingrequest" ("trip_id");

CREATE TABLE "auth_group" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(150) NOT NULL UNIQUE);

CREATE TABLE "auth_group_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "auth_permission" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "content_type_id" integer NOT NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "codename" varchar(100) NOT NULL, "name" varchar(255) NOT NULL);

CREATE TABLE "auth_user" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "password" varchar(128) NOT NULL, "last_login" datetime NULL, "is_superuser" bool NOT NULL, "username" varchar(150) NOT NULL UNIQUE, "last_name" varchar(150) NOT NULL, "email" varchar(254) NOT NULL, "is_staff" bool NOT NULL, "is_active" bool NOT NULL, "date_joined" datetime NOT NULL, "first_name" varchar(150) NOT NULL);

CREATE TABLE "auth_user_groups" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "group_id" integer NOT NULL REFERENCES "auth_group" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "auth_user_user_permissions" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "permission_id" integer NOT NULL REFERENCES "auth_permission" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "django_admin_log" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "object_id" text NULL, "object_repr" varchar(200) NOT NULL, "action_flag" smallint unsigned NOT NULL CHECK ("action_flag" >= 0), "change_message" text NOT NULL, "content_type_id" integer NULL REFERENCES "django_content_type" ("id") DEFERRABLE INITIALLY DEFERRED, "user_id" integer NOT NULL REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED, "action_time" datetime NOT NULL);

CREATE TABLE "django_content_type" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app_label" varchar(100) NOT NULL, "model" varchar(100) NOT NULL);

CREATE TABLE "django_migrations" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "app" varchar(255) NOT NULL, "name" varchar(255) NOT NULL, "applied" datetime NOT NULL);

CREATE TABLE "django_session" ("session_key" varchar(40) NOT NULL PRIMARY KEY, "session_data" text NOT NULL, "expire_date" datetime NOT NULL);

CREATE TABLE sqlite_sequence(name,seq);

CREATE TABLE "tracking_bus" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "registration_number" varchar(20) NOT NULL UNIQUE, "current_lat" real NULL, "current_lng" real NULL, "speed" real NOT NULL, "last_updated" datetime NOT NULL, "current_stop_time_id" bigint NULL REFERENCES "tracking_stoptime" ("id") DEFERRABLE INITIALLY DEFERRED, "current_trip_id" varchar(100) NULL REFERENCES "tracking_trip" ("trip_id") DEFERRABLE INITIALLY DEFERRED, "status" varchar(20) NOT NULL, "is_active" bool NOT NULL);

CREATE TABLE "tracking_driver" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "is_active" bool NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tracking_driverbusassignment" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "is_active" bool NOT NULL, "assigned_at" datetime NOT NULL, "bus_id" bigint NOT NULL REFERENCES "tracking_bus" ("id") DEFERRABLE INITIALLY DEFERRED, "driver_id" bigint NOT NULL REFERENCES "tracking_driver" ("id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_driver_bus_assignment" UNIQUE ("driver_id", "bus_id"));

CREATE TABLE "tracking_passenger" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "name" varchar(100) NOT NULL, "last_updated" datetime NOT NULL, "user_id" integer NOT NULL UNIQUE REFERENCES "auth_user" ("id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tracking_route" ("route_id" varchar(50) NOT NULL PRIMARY KEY, "route_long_name" varchar(255) NOT NULL, "continuous_pickup" integer NOT NULL, "continuous_drop_off" integer NOT NULL);

CREATE TABLE "tracking_shape" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "shape_id" varchar(100) NOT NULL, "shape_pt_lat" real NOT NULL, "shape_pt_lon" real NOT NULL, "shape_pt_sequence" integer NOT NULL, CONSTRAINT "unique_shape_point" UNIQUE ("shape_id", "shape_pt_sequence"));

CREATE TABLE "tracking_stop" ("stop_id" integer NOT NULL PRIMARY KEY, "stop_name" varchar(255) NOT NULL, "stop_lat" real NOT NULL, "stop_lon" real NOT NULL);

CREATE TABLE "tracking_stoptime" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "stop_sequence" integer NOT NULL, "stop_id" integer NOT NULL REFERENCES "tracking_stop" ("stop_id") DEFERRABLE INITIALLY DEFERRED, "trip_id" varchar(100) NOT NULL REFERENCES "tracking_trip" ("trip_id") DEFERRABLE INITIALLY DEFERRED, CONSTRAINT "unique_stop_sequence_per_trip" UNIQUE ("trip_id", "stop_sequence"));

CREATE TABLE "tracking_trip" ("trip_id" varchar(100) NOT NULL PRIMARY KEY, "trip_headsign" varchar(255) NOT NULL, "direction_id" integer NOT NULL, "shape_id" varchar(100) NOT NULL, "service_id" varchar(100) NOT NULL, "route_id" varchar(50) NOT NULL REFERENCES "tracking_route" ("route_id") DEFERRABLE INITIALLY DEFERRED);

CREATE TABLE "tracking_waitingrequest" ("id" integer NOT NULL PRIMARY KEY AUTOINCREMENT, "status" varchar(20) NOT NULL, "created_at" datetime NOT NULL, "deactivated_at" datetime NULL, "passenger_id" bigint NOT NULL REFERENCES "tracking_passenger" ("id") DEFERRABLE INITIALLY DEFERRED, "stop_id" integer NOT NULL REFERENCES "tracking_stop" ("stop_id") DEFERRABLE INITIALLY DEFERRED, "trip_id" varchar(100) NOT NULL REFERENCES "tracking_trip" ("trip_id") DEFERRABLE INITIALLY DEFERRED);
