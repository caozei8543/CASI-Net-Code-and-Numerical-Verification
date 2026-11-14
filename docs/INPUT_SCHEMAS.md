# Required experimental records

- **event_confusions.csv**: `dataset,parent_event_uid,split,seed,method,run_id,tp,fp,tn,fn,valid_mask_sha256,reference_mask_sha256,prediction_sha256`
- **ablation_per_event.csv**: `dataset,parent_event_uid,split,seed,configuration,f1,valid_mask_sha256,prediction_sha256`
- **contour_candidates.csv**: `parent_event_uid,split,state,candidate_id,is_genuine,is_false,is_test_eligible,p_value,rejected,terrain_group,source_core_present,anchor_count,geometry_status`
- **hecras_reference_sites.csv**: `parent_event_uid,site_id,output_type,configuration,reference_m,pred_m,lower90_m,upper90_m,valid,exclusion_reason,vertical_datum,sensor_time_utc,reference_time_utc,reference_source_id,prediction_run_id`
- **hecras_models.csv**: `parent_event_uid,hecras_version,model_archive_sha256,mesh_sha256,geometry_source,terrain_dem_id,vertical_datum,mesh_base_m,mesh_refinement_m,time_step_min_s,time_step_max_s,upstream_hydrograph_id,downstream_stage_id,manning_channel_min,manning_channel_max,manning_floodplain_min,manning_floodplain_max,solver_log_sha256`
- **gauge_checks.csv**: `parent_event_uid,gauge_id,gauge_time_utc,coordinate_crs,x,y,vertical_datum,observed_stage_m,simulated_stage_m,used_for_forcing,used_for_calibration,observation_source_id`
- **contour_group_diagnostics.csv**: `state,terrain_group,n_reference_candidates,n_genuine,n_false,n_testable,n_rejected_genuine,n_rejected_false,n_eligible_events,source_run_id`
- **runtime_logs.csv**: `run_id,scene_id,valid_pixels,hardware,cpu_cores,peak_ram_gb,peak_gpu_gb,contour_seconds,joint_uq_seconds,total_seconds,timing_excludes_io,timing_excludes_offline_calibration`
- **failure_cases.csv**: `case_id,parent_event_uid,failure_mode,optical_product_id,sar_product_id,dem_id,reference_mask_id,observability_state,source_core_present,mask_sha256,figure_source_path,evidence_uri,review_status`
- **file_index.csv**: `artifact_id,relative_path,sha256,source_provenance,license_or_access,created_utc,role`

All scientific record tables are header-only until populated from the original data.
