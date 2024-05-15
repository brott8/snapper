from operator import itemgetter


def create_apprise_report(report_data):
    sync_job_ran, scrub_job_ran, sync_job_time, scrub_job_time, diff_data, zero_subsecond_count, \
        scrub_stats, drive_stats, smart_drive_data, global_fp, total_time = itemgetter(
        'sync_job_ran',
        'scrub_job_ran',
        'sync_job_time',
        'scrub_job_time',
        'diff_data',
        'zero_subsecond_count',
        'scrub_stats',
        'drive_stats',
        'smart_drive_data',
        'global_fp',
        'total_time')(report_data)

    #
    # Create email report

    sync_report = f'**Sync Job**'

    if sync_job_ran:
        sync_report = sync_report + f'''
        Job finished successfully in {sync_job_time}.
        File diff summary as follows:
        - {diff_data["added"]} added
        - {diff_data["removed"]} removed
        - {diff_data["updated"]} updated
        - {diff_data["moved"]} moved
        - {diff_data["copied"]} copied
        - {diff_data["restored"]} restored
        '''
    else:
        sync_report = sync_report + 'Sync job did **not** run.'

    touch_report = '**Touch job**'

    if zero_subsecond_count > 0:
        touch_report = touch_report + f'''
        'A total of {zero_subsecond_count} file(s) had their sub-second value fixed.
        '''
    else:
        touch_report = touch_report + 'No zero sub-second files were found.'

    scrub_report = '**Scrub Job**'

    if scrub_job_ran:
        scrub_report = scrub_report + f'''
        Job finished successfully in {scrub_job_time}.
        {scrub_stats["unscrubbed"]}% of the array has not been scrubbed, with the oldest block at {scrub_stats["scrub_age"]} day(s).
        '''
    # , the median at {scrub_stats["median"]} day(s), and the newest at {scrub_stats["newest"]} day(s).
    else:
        scrub_report = scrub_report + 'Scrub Job did **not** run.'

    array_drive_report = ''.join(f'''
    <tr class="{"array_stats" if not d["drive_name"] else ''}">
        <td>{d["drive_name"] if d["drive_name"] else 'Full Array'}</td>
        <td>{d["fragmented_files"]}</td>
        <td>{d["excess_fragments"]}</td>
        <td>{d["wasted_gb"]}</td>
        <td>{d["used_gb"]}</td>
        <td>{d["free_gb"]}</td>
        <td>{d["use_percent"]}</td>
    </tr>
    ''' for d in drive_stats)

    array_report = f'''
    <h3>SnapRAID Array Report</h3>
    <table>
        <thead>
            <tr>
                <th>Drive</th>
                <th>Fragmented Files</th>
                <th>Excess Fragments</th>
                <th>Wasted Space (GB)</th>
                <th>Used Space (GB)</th>
                <th>Free Space (GB)</th>
                <th>Total Used (%)</th>
            </tr>
        </thead>
        <tbody>
            {array_drive_report}
        </tbody>
    </table>
    '''

    smart_drive_report = ''.join(f'''
    <tr>
        <td>{d["disk"]} ({d["device"]})</td>
        <td>{d["temp"]}</td>
        <td>{d["power_on_days"]}</td>
        <td>{d["error_count"]}</td>
        <td>{d["fp"]}</td>
        <td>{d["size"]}</td>
        <td>{d["serial"]}</td>
    </tr>
    ''' for d in smart_drive_data)

    smart_report = f'''
    <h3>SMART Report</h3>
    <table>
        <thead>
            <tr>
                <th>Drive</th>
                <th>Temperature (°C)</th>
                <th>Power On Time (days)</th>
                <th>Error Count</th>
                <th>Failure Probability</th>
                <th>Drive Size (TiB)</th>
                <th>Serial Number</th>
            </tr>
        </thead>
        <tbody>
            {smart_drive_report}
        </tbody>
    </table>
    <p>The current failure probability of any single drive this year is <strong>{global_fp}%</strong>.</p>
    '''

    # Check if any drive had an error count
    drives_with_errors = []
    for drive in smart_drive_data:
        error_count = drive.get("error_count")
        if isinstance(error_count, str) and error_count.isdigit():
            error_count = int(error_count)
        if isinstance(error_count, int) and error_count > 0:
            drive["error_count"] = error_count
            drives_with_errors.append(drive)

    # Summarize SMART drive report
    smart_summary = f'**SMART Summary**\nFailure Probability: {global_fp}%'

    if drives_with_errors:
        smart_summary += "\nDrives with errors:"
        for drive in drives_with_errors:
            smart_summary += f"\n- {drive['disk']} ({drive['device']}) - Error Count: {drive['error_count']}"

    email_report = f'''SnapRAID job completed successfully in {total_time}
    {touch_report} 
    {sync_report}
    {scrub_report}
    {smart_summary}
    '''

    return email_report
