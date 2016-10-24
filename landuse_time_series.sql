/* Creates a new table storing the total area of landuse 11 - 
high density residential (less than 1/4 acre) - over the four decades. 
Columns are years (1971, 1985, 1999, 2005), rows are municipality/town ID's */
SELECT 
	lu_1971.TOWN_ID,
	lu_1971.TOWN,
	lu_1971.highdenres_1971,
	lu_1985.highdenres_1985,
	lu_1999.highdenres_1999,
	lu_2005.highdenres_2005
FROM 
	(SELECT 
		TOWN_ID,
		TOWN,
		SUM(AREA) AS highdenres_1971 
	FROM 
		landuse_1971_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU21_1971 = 11 
		AND 
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1971
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS highdenres_1985 
	FROM landuse_1985_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1985 = 11 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1985
ON lu_1971.TOWN_ID = lu_1985.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS highdenres_1999 
	FROM landuse_1999_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1999 = 11
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_1999
ON lu_1971.TOWN_ID = lu_1999.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS highdenres_2005 
	FROM landuse_2005_Half 
	WHERE 
		LandUse2005_Slope_Clip_LUCODE = 11 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_2005
ON lu_1971.TOWN_ID = lu_2005.TOWN_ID
GROUP BY lu_1971.TOWN_ID;

/* Creates a new table storing the total area of landuse 10 - 
multi-family residential - over the four decades. 
Columns are years (1971, 1985, 1999, 2005), rows are municipality/town ID's */
SELECT 
	lu_1971.TOWN_ID,
	lu_1971.TOWN,
	lu_1971.multifam_1971,
	lu_1985.multifam_1985,
	lu_1999.multifam_1999,
	lu_2005.multifam_2005
FROM 
	(SELECT 
		TOWN_ID,
		TOWN,
		SUM(AREA) AS multifam_1971 
	FROM 
		landuse_1971_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU21_1971 = 10 
		AND 
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1971
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS multifam_1985 
	FROM landuse_1985_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1985 = 10 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1985
ON lu_1971.TOWN_ID = lu_1985.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS multifam_1999 
	FROM landuse_1999_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1999 = 10
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_1999
ON lu_1971.TOWN_ID = lu_1999.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS multifam_2005 
	FROM landuse_2005_Half 
	WHERE 
		LandUse2005_Slope_Clip_LUCODE = 10 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_2005
ON lu_1971.TOWN_ID = lu_2005.TOWN_ID
GROUP BY lu_1971.TOWN_ID;

/* Creates a new table storing the total area of landuse 15 - 
commercial - over the four decades. 
Columns are years (1971, 1985, 1999, 2005), rows are municipality/town ID's */
SELECT 
	lu_1971.TOWN_ID,
	lu_1971.TOWN,
	lu_1971.commercial_1971,
	lu_1985.commercial_1985,
	lu_1999.commercial_1999,
	lu_2005.commercial_2005
FROM 
	(SELECT 
		TOWN_ID,
		TOWN,
		SUM(AREA) AS commercial_1971 
	FROM 
		landuse_1971_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU21_1971 = 15 
		AND 
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1971
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS commercial_1985 
	FROM landuse_1985_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1985 = 15 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1
	GROUP BY TOWN_ID) lu_1985
ON lu_1971.TOWN_ID = lu_1985.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS commercial_1999 
	FROM landuse_1999_Half 
	WHERE 
		LANDUSE_Slope_Clip_LU37_1999 = 15
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_1999
ON lu_1971.TOWN_ID = lu_1999.TOWN_ID
JOIN
	(SELECT 
		TOWN_ID, 
		SUM(AREA) AS commercial_2005 
	FROM landuse_2005_Half 
	WHERE 
		LandUse2005_Slope_Clip_LUCODE = 15 
		AND
		MassGIS_Dev_Undev_LU_Ref_Not_Dev != 1 
	GROUP BY TOWN_ID) lu_2005
ON lu_1971.TOWN_ID = lu_2005.TOWN_ID
GROUP BY lu_1971.TOWN_ID;
