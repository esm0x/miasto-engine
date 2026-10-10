package com.adminstack.miasto.ui.more

import org.junit.Assert.assertEquals
import org.junit.Test

class SupportLinksTest {

    @Test
    fun `a new issue starts with the city, encoded for a URL`() {
        assertEquals(
            "https://github.com/esm0x/miasto-engine/issues/new?title=%5BLubomia%5D%20",
            newIssueUrl("https://github.com/esm0x/miasto-engine", "Lubomia"),
        )
        assertEquals(
            "https://github.com/x/y/issues/new?title=%5BJastrz%C4%99bie-Zdr%C3%B3j%5D%20",
            newIssueUrl("https://github.com/x/y", "Jastrzębie-Zdrój"),
        )
    }
}
